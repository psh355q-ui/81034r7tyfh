-- 생성된 인덱스 확인 쿼리
SELECT tablename, indexname, pg_size_pretty(
        pg_relation_size(indexname::regclass)
    ) as size
FROM pg_indexes
WHERE
    schemaname = 'public'
    AND (
        indexname LIKE '%ticker%date%'
        OR indexname LIKE '%processed%'
        OR indexname LIKE '%pending%alert%'
    )
ORDER BY tablename, indexname;