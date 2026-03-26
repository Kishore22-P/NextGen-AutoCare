import psycopg2
from psycopg2.extras import DictCursor

conn = psycopg2.connect(host='localhost', database='vehicle_service', user='postgres', password='password', cursor_factory=DictCursor)
cur = conn.cursor()

print("=== Services 35-40 (Revenue Report rows) ===")
cur.execute("""
    SELECT s.id, s.parts_cost, s.labor_cost, s.wash_cost, s.tech_commission, s.center_share, s.payment_status
    FROM services s
    WHERE s.id BETWEEN 35 AND 40
    ORDER BY s.id DESC
""")
for r in cur.fetchall():
    print(f"SRV-{r['id']}: parts={r['parts_cost']} labor={r['labor_cost']} wash={r['wash_cost']} tech_share={r['tech_commission']} center_share={r['center_share']} status={r['payment_status']}")

conn.close()
print("Done.")
