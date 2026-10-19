-- Run against tables loaded from data/customers.csv and data/transactions.csv

-- 1. Structuring candidates: deposits just below the 10,000 threshold
SELECT customer_id, COUNT(*) AS near_threshold_deposits, SUM(amount) AS total_amount
FROM transactions
WHERE direction = 'in' AND amount BETWEEN 9000 AND 9999.99
GROUP BY customer_id HAVING COUNT(*) >= 3 ORDER BY near_threshold_deposits DESC;

-- 2. Exposure to higher-risk jurisdictions by customer country
SELECT c.country, COUNT(*) AS txns, SUM(t.amount) AS value
FROM transactions t JOIN customers c USING (customer_id)
WHERE t.counterparty_country IN ('KP','IR','MM')
GROUP BY c.country ORDER BY value DESC;

-- 3. KYC documentation gaps by entity type
SELECT entity_type,
       SUM(CASE WHEN id_doc_missing THEN 1 ELSE 0 END)            AS missing_id,
       SUM(CASE WHEN address_proof_missing THEN 1 ELSE 0 END)     AS missing_address,
       SUM(CASE WHEN beneficial_owner_missing THEN 1 ELSE 0 END)  AS missing_beneficial_owner
FROM customers GROUP BY entity_type;
