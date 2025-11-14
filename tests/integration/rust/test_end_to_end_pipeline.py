"""
End-to-end pipeline test for Rust parsing.

Tests the complete flow: Rust code → parsing → actions → endpoint generation.
"""

import pytest
import tempfile
from pathlib import Path
from src.reverse_engineering.rust_parser import RustReverseEngineeringService
from src.reverse_engineering.rust_action_parser import RustActionParser


class TestEndToEndPipeline:
    """Test the complete Rust parsing pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = RustReverseEngineeringService()
        self.action_parser = RustActionParser()

    def test_full_pipeline_user_management(self):
        """Test complete pipeline from Rust CRUD code to SpecQL actions and endpoints."""
        # Use a simplified version of the working comprehensive test code
        rust_code = """
use diesel::prelude::*;
use actix_web::{web, HttpResponse, Result as ActixResult};
use serde::{Deserialize, Serialize};

table! {
    users (id) {
        id -> Integer,
        username -> Text,
        email -> Nullable<Text>,
    }
}

#[derive(Debug, Clone, Queryable, Insertable, AsChangeset)]
#[diesel(table_name = users)]
pub struct User {
    pub id: i32,
    pub username: String,
    pub email: Option<String>,
}

impl User {
    pub fn create(&self, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        diesel::insert_into(users::table)
            .values(self)
            .get_result(conn)
    }

    pub fn find(id: i32, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        users::table.find(id).first(conn)
    }

    pub fn update(&self, conn: &mut PgConnection) -> diesel::QueryResult<Self> {
        diesel::update(users::table.find(self.id))
            .set(self)
            .get_result(conn)
    }

    pub fn delete(id: i32, conn: &mut PgConnection) -> diesel::QueryResult<usize> {
        diesel::delete(users::table.find(id)).execute(conn)
    }
}

#[get("/users")]
pub async fn get_users() -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(vec!["user1", "user2"]))
}

#[post("/users")]
pub async fn create_user() -> ActixResult<HttpResponse> {
    Ok(HttpResponse::Created().json(serde_json::json!({"id": 1})))
}

#[get("/users/{id}")]
pub async fn get_user(path: web::Path<i32>) -> ActixResult<HttpResponse> {
    let user_id = path.into_inner();
    Ok(HttpResponse::Ok().json(serde_json::json!({"id": user_id})))
}

pub type PgConnection = diesel::PgConnection;
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # Step 1: Parse Rust code to entities
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Should have User entity
            assert len(entities) >= 1
            user_entity = next((e for e in entities if e.name == "User"), None)
            assert user_entity is not None, "User entity not found"

            # Verify User entity structure
            assert user_entity.table == "user"  # SpecQL singularizes table names
            assert len(user_entity.fields) == 3  # id, username, email
            assert "id" in user_entity.fields
            assert "username" in user_entity.fields
            assert "email" in user_entity.fields

            # Step 2: Extract actions from Rust code
            actions = self.action_parser.extract_actions(Path(temp_path))

            # Should have CRUD actions from impl block + route handlers
            assert len(actions) >= 7  # 4 CRUD methods + 3 route handlers

            action_names = [a["name"] for a in actions]

            # CRUD operations from impl block
            crud_actions = ["create", "find", "update", "delete"]
            for action in crud_actions:
                assert action in action_names, f"Missing CRUD action: {action}"

            # Route handler actions
            route_actions = [
                "get_users",
                "create_user",
                "get_user",
            ]
            for action in route_actions:
                assert action in action_names, f"Missing route action: {action}"

            # Step 3: Simulate endpoint generation from actions
            # This would typically be done by the SpecQL action-to-endpoint mapping
            endpoints = self._simulate_endpoint_generation(actions)

            # Verify endpoints were generated
            assert len(endpoints) >= 5

            # Check specific endpoints
            get_users_ep = next(
                (
                    ep
                    for ep in endpoints
                    if ep["path"] == "/users" and ep["method"] == "GET"
                ),
                None,
            )
            assert get_users_ep is not None, "GET /users endpoint not generated"

            post_users_ep = next(
                (
                    ep
                    for ep in endpoints
                    if ep["path"] == "/users" and ep["method"] == "POST"
                ),
                None,
            )
            assert post_users_ep is not None, "POST /users endpoint not generated"

            get_user_ep = next(
                (
                    ep
                    for ep in endpoints
                    if "/users/{id}" in ep["path"] and ep["method"] == "GET"
                ),
                None,
            )
            assert get_user_ep is not None, "GET /users/{id} endpoint not generated"

            put_user_ep = next(
                (
                    ep
                    for ep in endpoints
                    if "/users/{id}" in ep["path"] and ep["method"] == "PUT"
                ),
                None,
            )
            assert put_user_ep is not None, "PUT /users/{id} endpoint not generated"

            delete_user_ep = next(
                (
                    ep
                    for ep in endpoints
                    if "/users/{id}" in ep["path"] and ep["method"] == "DELETE"
                ),
                None,
            )
            assert delete_user_ep is not None, (
                "DELETE /users/{id} endpoint not generated"
            )

            print(f"\n✅ End-to-end pipeline test passed!")
            print(f"   - Parsed {len(entities)} entities")
            print(f"   - Extracted {len(actions)} actions")
            print(f"   - Generated {len(endpoints)} endpoints")
            print(
                f"   - Endpoints: {', '.join([f'{ep['method']} {ep['path']}' for ep in endpoints])}"
            )

        finally:
            import os

            os.unlink(temp_path)

    def _simulate_endpoint_generation(self, actions):
        """Simulate endpoint generation from actions (simplified version)."""
        endpoints = []

        for action in actions:
            if "http_method" in action and "path" in action:
                # Direct route handler
                endpoints.append(
                    {
                        "method": action["http_method"],
                        "path": action["path"],
                        "action": action["name"],
                        "type": "route_handler",
                    }
                )
            elif action["type"] in ["create", "read", "update", "delete"]:
                # CRUD action - generate REST endpoint
                if action["type"] == "create":
                    endpoints.append(
                        {
                            "method": "POST",
                            "path": "/users",
                            "action": action["name"],
                            "type": "crud",
                        }
                    )
                elif action["type"] == "read":
                    if len(action.get("parameters", [])) == 1:
                        # Read single item
                        endpoints.append(
                            {
                                "method": "GET",
                                "path": "/users/{id}",
                                "action": action["name"],
                                "type": "crud",
                            }
                        )
                    else:
                        # Read collection
                        endpoints.append(
                            {
                                "method": "GET",
                                "path": "/users",
                                "action": action["name"],
                                "type": "crud",
                            }
                        )
                elif action["type"] == "update":
                    endpoints.append(
                        {
                            "method": "PUT",
                            "path": "/users/{id}",
                            "action": action["name"],
                            "type": "crud",
                        }
                    )
                elif action["type"] == "delete":
                    endpoints.append(
                        {
                            "method": "DELETE",
                            "path": "/users/{id}",
                            "action": action["name"],
                            "type": "crud",
                        }
                    )

        return endpoints


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
