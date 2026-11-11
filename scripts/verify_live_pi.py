import sys
import exec_pi

script = """
echo "=== 1. SERVICES STATUS ==="
for s in omni-hub omniroute omniroute-tunnel hermes-dashboard fan-control; do
    echo -n "${s}: "
    systemctl is-active "${s}"
done

echo ""
echo "=== 2. LOCAL HTTP PORT 8000 CHECK ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000/login/

echo ""
echo "=== 3. JOB OPPORTUNITIES IN PI DATABASE ==="
python3 /home/arush/omni_hub/manage.py shell -c "from growth.models import JobOpportunity; print('Total Jobs in DB:', JobOpportunity.objects.count()); print('High Matches (>=80%):', JobOpportunity.objects.filter(match_score__gte=80).count())"

echo ""
echo "=== 4. TEST SENTINEL AUDIT ONLY ==="
python3 /home/arush/omni_growth_sentinel.py --audit-only

echo ""
echo "=== 5. PI TEMPERATURE & RAM ==="
vcgencmd measure_temp
free -h
"""

code, out, err = exec_pi.run_remote(script)
print(out)
if err:
    print("STDERR:", err)

