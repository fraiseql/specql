from reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestEventSourcingPattern:
    """Test event sourcing pattern detection across all languages"""

    def test_sql_event_store(self):
        """Detect event store in SQL"""
        code = """
        CREATE TABLE events (
            id SERIAL PRIMARY KEY,
            aggregate_id UUID NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB NOT NULL,
            version INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            CONSTRAINT unique_version UNIQUE (aggregate_id, version)
        );

        CREATE INDEX idx_events_aggregate ON events(aggregate_id);
        CREATE INDEX idx_events_type ON events(event_type);

        INSERT INTO events (aggregate_id, event_type, event_data, version)
        VALUES ($1, 'ContactCreated', $2, $3);
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "sql")

        event_sourcing = [p for p in patterns if p.name == "event_sourcing"]
        assert len(event_sourcing) == 1
        assert event_sourcing[0].confidence >= 0.85
        assert "event store table" in str(event_sourcing[0].evidence).lower()

    def test_python_event_replay(self):
        """Detect event replay in Python"""
        code = """
        from dataclasses import dataclass
        from uuid import UUID
        import json

        @dataclass
        class Event:
            aggregate_id: UUID
            event_type: str
            event_data: dict
            version: int

        class ContactAggregate:
            def __init__(self, aggregate_id: UUID):
                self.aggregate_id = aggregate_id
                self.version = 0
                self.events = []

            def apply_event(self, event: Event):
                # Replay event to rebuild state
                if event.event_type == 'ContactCreated':
                    self._apply_contact_created(event.event_data)
                elif event.event_type == 'ContactUpdated':
                    self._apply_contact_updated(event.event_data)
                self.version = event.version

            def load_from_history(self, events: list[Event]):
                # Rebuild aggregate from event history
                for event in events:
                    self.apply_event(event)
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "python")

        event_sourcing = [p for p in patterns if p.name == "event_sourcing"]
        assert len(event_sourcing) == 1
        assert event_sourcing[0].confidence >= 0.85

    def test_java_event_versioning(self):
        """Detect event versioning in Java"""
        code = """
        import java.util.UUID;
        import java.time.Instant;

        public class Event {
            private UUID aggregateId;
            private String eventType;
            private String eventData;
            private int version;
            private Instant createdAt;

            public Event(UUID aggregateId, String eventType, String eventData, int version) {
                this.aggregateId = aggregateId;
                this.eventType = eventType;
                this.eventData = eventData;
                this.version = version;
                this.createdAt = Instant.now();
            }
        }

        public class EventStore {
            public void appendEvent(Event event) {
                // Append-only event store
                eventRepository.save(event);
            }

            public List<Event> getEventsByAggregate(UUID aggregateId) {
                return eventRepository.findByAggregateIdOrderByVersionAsc(aggregateId);
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "java")

        assert any(p.name == "event_sourcing" and p.confidence >= 0.80 for p in patterns)

    def test_rust_event_append(self):
        """Detect event append in Rust"""
        code = """
        use uuid::Uuid;
        use serde::{Serialize, Deserialize};

        #[derive(Debug, Clone, Serialize, Deserialize)]
        pub struct Event {
            pub aggregate_id: Uuid,
            pub event_type: String,
            pub event_data: serde_json::Value,
            pub version: i32,
        }

        pub struct EventStore {
            events: Vec<Event>,
        }

        impl EventStore {
            pub async fn append_event(&mut self, event: Event) -> Result<(), Error> {
                // Append-only operation
                self.events.push(event);
                Ok(())
            }

            pub async fn get_events(&self, aggregate_id: Uuid) -> Vec<Event> {
                self.events
                    .iter()
                    .filter(|e| e.aggregate_id == aggregate_id)
                    .cloned()
                    .collect()
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "rust")

        assert any(p.name == "event_sourcing" for p in patterns)
