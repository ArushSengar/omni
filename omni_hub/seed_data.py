import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omni_hub.settings')
django.setup()

from growth.models import GrowthPost, ResearchTopic, SystemStatus

def seed():
    if not GrowthPost.objects.exists():
        GrowthPost.objects.create(
            title="Linux Privilege Escalation via SUID Binaries (TryHackMe Lab)",
            domain="Cyber Security & Systems",
            source="assignment-07",
            linkedin_content=(
                "Today’s focus: Linux Privilege Escalation via SUID Binaries.\n"
                "When a binary has SUID set (chmod u+s), it executes with the file owner's permissions—often root. "
                "If that binary is vulnerable or has command execution escapes, it becomes an instant escalation vector.\n\n"
                "Enumeration command used:\n"
                "find / -perm -u=s -type f 2>/dev/null\n\n"
                "Found misconfigured binary and escalated shell to root privileges (euid=0)."
            ),
            twitter_content="Mastering Linux PrivEsc requires methodical enumeration. Check SUID binaries, sudo misconfigs, cron jobs, and writable files. #LinuxSecurity #TryHackMe",
            status="PUBLISHED",
            linkedin_urn="urn:li:share:7392176841285222400",
            twitter_url="https://x.com/arushcyber/status/1986426463991206101",
            likes=14,
            views=385,
            comments=5
        )
        print("Created sample GrowthPost")

    if not ResearchTopic.objects.exists():
        ResearchTopic.objects.create(
            title="eBPF Security Telemetry & Kernel Tracing",
            category="Cyber Security",
            technical_problem="Traditional auditd produces high CPU overhead under heavy process spawning workloads.",
            commands="bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf(\"%s -> %s\\n\", comm, str(args->filename)); }'",
            solution="Hook into raw kernel tracepoints using eBPF ring buffers for zero-overhead user-space execution monitoring.",
            impact="85% reduction in monitoring CPU overhead with microsecond-level accuracy.",
            tags="ebpf, linux, tracing, kernel, security",
            is_used=False
        )
        ResearchTopic.objects.create(
            title="Linux zram with zstd Compression for 4GB Homelabs",
            category="Linux Kernel & Performance",
            technical_problem="RAM thrashing on Raspberry Pi 4 running multiple Docker microservices and LLM workers.",
            commands="sudo zramctl --find --size 2G --algorithm zstd; sudo mkswap /dev/zram0; sudo swapon -p 32767 /dev/zram0",
            solution="Deploy compressed in-memory swap block device using zstd algorithm with higher priority than physical storage.",
            impact="Triples effective available memory without SSD disk thrashing.",
            tags="zram, kernel, swap, homelab, rpi4",
            is_used=False
        )
        print("Created sample ResearchTopics")

    if not SystemStatus.objects.exists():
        SystemStatus.objects.create(
            pi_uptime="14 days, 6 hours",
            pi_ram_free="1.8 GB / 3.8 GB (47%)",
            omniroute_status="Active (Port 20128)"
        )
        print("Created SystemStatus")

if __name__ == "__main__":
    seed()

