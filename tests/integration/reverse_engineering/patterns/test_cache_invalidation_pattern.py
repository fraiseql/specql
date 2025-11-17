import pytest
from src.reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestCacheInvalidationPattern:
    """Test cache invalidation pattern detection across all languages"""

    def test_python_cache_invalidation(self):
        """Detect cache invalidation in Python"""
        code = """
        import redis

        class ContactCache:
            def __init__(self, redis_client):
                self.redis = redis_client

            def get_contact(self, contact_id: int):
                cache_key = f"contact:{contact_id}"
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
                return None

            def invalidate_contact(self, contact_id: int):
                cache_key = f"contact:{contact_id}"
                self.redis.delete(cache_key)

            def invalidate_by_tag(self, tag: str):
                # Tag-based cache invalidation
                pattern = f"*:{tag}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "python")
        assert any(p.name == "cache_invalidation" and p.confidence >= 0.82 for p in patterns)

    def test_java_cache_expiration(self):
        """Detect cache expiration in Java"""
        code = """
        import com.google.common.cache.Cache;
        import com.google.common.cache.CacheBuilder;
        import java.util.concurrent.TimeUnit;

        @Service
        public class ContactCacheService {
            private Cache<String, Contact> contactCache;

            public ContactCacheService() {
                this.contactCache = CacheBuilder.newBuilder()
                    .maximumSize(10000)
                    .expireAfterWrite(30, TimeUnit.MINUTES)
                    .build();
            }

            public Contact getContact(String contactId) {
                return contactCache.getIfPresent(contactId);
            }

            public void invalidateContact(String contactId) {
                contactCache.invalidate(contactId);
            }

            public void invalidateAllContacts() {
                contactCache.invalidateAll();
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "java")
        assert any(p.name == "cache_invalidation" for p in patterns)

    def test_sql_cache_table(self):
        """Detect cache table invalidation in SQL"""
        code = """
        CREATE TABLE cache_entries (
            cache_key VARCHAR(255) PRIMARY KEY,
            cache_value TEXT,
            expires_at TIMESTAMP,
            tags TEXT[]
        );

        CREATE INDEX idx_cache_expires ON cache_entries(expires_at);
        CREATE INDEX idx_cache_tags ON cache_entries USING GIN(tags);

        -- Invalidate by key
        DELETE FROM cache_entries WHERE cache_key = $1;

        -- Invalidate by tag
        DELETE FROM cache_entries WHERE $1 = ANY(tags);

        -- Clean expired entries
        DELETE FROM cache_entries WHERE expires_at < NOW();
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "sql")
        assert any(p.name == "cache_invalidation" for p in patterns)

    def test_rust_cache_invalidation(self):
        """Detect cache invalidation in Rust"""
        code = """
        use std::collections::HashMap;
        use std::time::{Duration, Instant};

        pub struct CacheEntry<T> {
            pub value: T,
            pub expires_at: Instant,
        }

        pub struct ContactCache {
            cache: HashMap<String, CacheEntry<Contact>>,
        }

        impl ContactCache {
            pub fn get(&self, key: &str) -> Option<&Contact> {
                if let Some(entry) = self.cache.get(key) {
                    if entry.expires_at > Instant::now() {
                        Some(&entry.value)
                    } else {
                        None
                    }
                } else {
                    None
                }
            }

            pub fn invalidate(&mut self, key: &str) {
                self.cache.remove(key);
            }

            pub fn invalidate_pattern(&mut self, pattern: &str) {
                self.cache.retain(|k, _| !k.contains(pattern));
            }

            pub fn cleanup_expired(&mut self) {
                let now = Instant::now();
                self.cache.retain(|_, v| v.expires_at > now);
            }
        }
        """

        detector = UniversalPatternDetector()
        patterns = detector.detect(code, "rust")
        assert any(p.name == "cache_invalidation" for p in patterns)
