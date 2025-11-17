import pytest
from src.reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestShardingPattern:
    """Test sharding pattern detection across all languages"""

    def test_sql_shard_key(self):
        """Detect shard key in SQL"""
        code = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            shard_key INTEGER NOT NULL,
            email VARCHAR(255),
            created_at TIMESTAMP
        );

        CREATE INDEX idx_shard_key ON contacts(shard_key);

        CREATE FUNCTION get_shard(p_id INTEGER) RETURNS INTEGER AS $$
        BEGIN
            RETURN p_id % 16;  -- 16 shards
        END;
        $$ LANGUAGE plpgsql;
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "sql")
        assert any(p.name == "sharding" and p.confidence >= 0.80 for p in patterns)

    def test_python_consistent_hashing(self):
        """Detect consistent hashing in Python"""
        code = """
        import hashlib

        class ShardRouter:
            def __init__(self, num_shards: int = 16):
                self.num_shards = num_shards

            def get_shard(self, key: str) -> int:
                # Consistent hashing for shard selection
                hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
                return hash_value % self.num_shards

            def route_query(self, contact_id: int):
                shard_id = self.get_shard(str(contact_id))
                return self.connections[shard_id]
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "python")
        assert any(p.name == "sharding" for p in patterns)

    def test_java_shard_routing(self):
        """Detect shard routing in Java"""
        code = """
        import java.util.List;
        import java.util.ArrayList;

        public class ShardManager {
            private List<DatabaseConnection> shards;
            private int numShards = 16;

            public ShardManager() {
                this.shards = new ArrayList<>();
                // Initialize shard connections
            }

            public DatabaseConnection getShard(String key) {
                int shardId = Math.abs(key.hashCode()) % numShards;
                return shards.get(shardId);
            }

            public void saveContact(Contact contact) {
                DatabaseConnection shard = getShard(contact.getEmail());
                shard.save(contact);
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "java")
        assert any(p.name == "sharding" for p in patterns)

    def test_rust_shard_distribution(self):
        """Detect shard distribution in Rust"""
        code = """
        use std::collections::HashMap;

        pub struct ShardRouter {
            num_shards: usize,
            connections: HashMap<usize, DatabaseConnection>,
        }

        impl ShardRouter {
            pub fn new(num_shards: usize) -> Self {
                let mut connections = HashMap::new();
                // Initialize connections...
                Self { num_shards, connections }
            }

            pub fn get_shard(&self, key: &str) -> usize {
                use std::collections::hash_map::DefaultHasher;
                use std::hash::{Hash, Hasher};

                let mut hasher = DefaultHasher::new();
                key.hash(&mut hasher);
                (hasher.finish() as usize) % self.num_shards
            }

            pub fn route(&self, contact_id: u64) -> &DatabaseConnection {
                let shard_id = self.get_shard(&contact_id.to_string());
                &self.connections[&shard_id]
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "rust")
        assert any(p.name == "sharding" for p in patterns)
