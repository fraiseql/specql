import pytest
from src.reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestRateLimitingPattern:
    """Test rate limiting pattern detection across all languages"""

    def test_java_rate_limiting(self):
        """Detect rate limiting in Java"""
        code = """
        import com.google.common.util.concurrent.RateLimiter;

        @RateLimited(requests = 100, window = "1 minute")
        public class ContactController {

            private final RateLimiter rateLimiter = RateLimiter.create(100.0);

            @PostMapping("/contacts")
            public Response createContact(@RequestBody ContactDTO dto) {
                if (!rateLimiter.tryAcquire()) {
                    throw new RateLimitExceededException("Too many requests");
                }

                // Create contact
                return Response.ok(contact).build();
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "java")
        assert any(p.name == "rate_limiting" for p in patterns)

    def test_python_token_bucket(self):
        """Detect token bucket rate limiting in Python"""
        code = """
        import time
        from collections import defaultdict

        class TokenBucket:
            def __init__(self, rate: float, capacity: int):
                self.rate = rate  # tokens per second
                self.capacity = capacity
                self.tokens = capacity
                self.last_update = time.time()
                self.buckets = defaultdict(lambda: {'tokens': capacity, 'last_update': time.time()})

            def consume(self, user_id: str, tokens: int = 1) -> bool:
                # Rate limiting logic
                now = time.time()
                bucket = self.buckets[user_id]

                # Refill tokens
                elapsed = now - bucket['last_update']
                refill = elapsed * self.rate
                bucket['tokens'] = min(self.capacity, bucket['tokens'] + refill)
                bucket['last_update'] = now

                # Check if enough tokens
                if bucket['tokens'] >= tokens:
                    bucket['tokens'] -= tokens
                    return True
                return False
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "python")
        assert any(p.name == "rate_limiting" for p in patterns)

    def test_sql_rate_limiting_table(self):
        """Detect rate limiting table in SQL"""
        code = """
        CREATE TABLE rate_limits (
            user_id VARCHAR(255) NOT NULL,
            action VARCHAR(100) NOT NULL,
            tokens_remaining INTEGER NOT NULL,
            last_refill TIMESTAMP NOT NULL,
            PRIMARY KEY (user_id, action)
        );

        CREATE FUNCTION check_rate_limit(
            p_user_id VARCHAR(255),
            p_action VARCHAR(100),
            p_cost INTEGER DEFAULT 1
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_record rate_limits%ROWTYPE;
            v_now TIMESTAMP := NOW();
            v_refill_amount INTEGER;
        BEGIN
            -- Get or create rate limit record
            SELECT * INTO v_record
            FROM rate_limits
            WHERE user_id = p_user_id AND action = p_action;

            IF NOT FOUND THEN
                INSERT INTO rate_limits (user_id, action, tokens_remaining, last_refill)
                VALUES (p_user_id, p_action, 99, v_now);
                RETURN TRUE;
            END IF;

            -- Refill tokens (simplified)
            v_refill_amount := EXTRACT(EPOCH FROM (v_now - v_record.last_refill))::INTEGER;
            v_record.tokens_remaining := LEAST(100, v_record.tokens_remaining + v_refill_amount);

            -- Check if enough tokens
            IF v_record.tokens_remaining >= p_cost THEN
                UPDATE rate_limits
                SET tokens_remaining = tokens_remaining - p_cost,
                    last_refill = v_now
                WHERE user_id = p_user_id AND action = p_action;
                RETURN TRUE;
            END IF;

            RETURN FALSE;
        END;
        $$ LANGUAGE plpgsql;
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "sql")
        assert any(p.name == "rate_limiting" for p in patterns)

    def test_rust_leaky_bucket(self):
        """Detect leaky bucket rate limiting in Rust"""
        code = """
        use std::collections::HashMap;
        use std::time::{Duration, Instant};

        pub struct LeakyBucket {
            capacity: usize,
            leak_rate: f64, // requests per second
            buckets: HashMap<String, BucketState>,
        }

        pub struct BucketState {
            pub water_level: f64,
            pub last_leak: Instant,
        }

        impl LeakyBucket {
            pub fn new(capacity: usize, leak_rate: f64) -> Self {
                Self {
                    capacity,
                    leak_rate,
                    buckets: HashMap::new(),
                }
            }

            pub fn allow(&mut self, key: &str) -> bool {
                let now = Instant::now();
                let state = self.buckets.entry(key.to_string()).or_insert(BucketState {
                    water_level: 0.0,
                    last_leak: now,
                });

                // Leak water
                let elapsed = now.duration_since(state.last_leak).as_secs_f64();
                state.water_level = (state.water_level - elapsed * self.leak_rate).max(0.0);
                state.last_leak = now;

                // Check if bucket has capacity
                if state.water_level < self.capacity as f64 {
                    state.water_level += 1.0;
                    true
                } else {
                    false
                }
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "rust")
        assert any(p.name == "rate_limiting" for p in patterns)
