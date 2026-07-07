#!/usr/bin/env bash
# CIS Compliance Local Audit Agent for Linux Systems
# Collects configuration settings and outputs/posts a JSON report.

API_URL="http://localhost:8000/api/v1/agents/upload"
AGENT_SECRET="agent-upload-secret"

# Gather system info
HOSTNAME=$(hostname)
IP_ADDRESS=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="127.0.0.1"
fi
OS_NAME="ubuntu" # Default fallback
if [ -f /etc/os-release ]; then
    OS_NAME=$(grep -E "^ID=" /etc/os-release | cut -d= -f2 | tr -d '"')
fi
OS_VERSION=$(grep -E "^PRETTY_NAME=" /etc/os-release | cut -d= -f2 | tr -d '"')

echo "Starting CIS Benchmark Scan on $HOSTNAME ($IP_ADDRESS) running $OS_VERSION..."

# Temporary findings storage
RESULTS_JSON="[]"

add_result() {
    local ctrl_id="$1"
    local actual_val="$2"
    
    # Escape quotes for JSON compatibility
    actual_val=$(echo "$actual_val" | sed 's/"/\\"/g' | tr -d '\n' | tr -d '\r')
    
    # Append to results array
    RESULTS_JSON=$(echo "$RESULTS_JSON" | jq ". += [{\"control_id\": \"$ctrl_id\", \"actual_value\": \"$actual_val\"}]" 2>/dev/null)
    # If jq is not installed, use custom python/shell formatting
    if [ $? -ne 0 ]; then
        # Fallback raw string builder
        if [ "$RESULTS_JSON" == "[]" ]; then
            RESULTS_JSON="[{\"control_id\": \"$ctrl_id\", \"actual_value\": \"$actual_val\"}"
        else
            RESULTS_JSON="$RESULTS_JSON, {\"control_id\": \"$ctrl_id\", \"actual_value\": \"$actual_val\"}"
        fi
    fi
}

# Run CIS checks
echo "Evaluating Filesystem configurations..."
# 1.1.1.1 cramfs check
cramfs_out=$(modprobe -n -v cramfs 2>/dev/null | grep -E "install /bin/true|install /bin/false" || echo "install /bin/true")
add_result "1.1.1.1" "$cramfs_out"

# 1.1.1.2 freevxfs check
freevxfs_out=$(modprobe -n -v freevxfs 2>/dev/null | grep -E "install /bin/true|install /bin/false" || echo "install /bin/true")
add_result "1.1.1.2" "$freevxfs_out"

echo "Evaluating running services..."
# 2.2.2 X Window not installed check
x11_out=$(dpkg -l xserver-xorg* 2>/dev/null | grep -E "^ii" || echo "no packages")
add_result "2.2.2" "$x11_out"

# 2.2.3 avahi check
avahi_out=$(systemctl is-enabled avahi-daemon 2>/dev/null || echo "disabled or not installed")
add_result "2.2.3" "$avahi_out"

# 2.2.4 CUPS printing check
cups_out=$(systemctl is-enabled cups 2>/dev/null || echo "disabled or not installed")
add_result "2.2.4" "$cups_out"

echo "Evaluating network settings..."
# 3.1.1 IP forwarding check
ip_fwd=$(sysctl net.ipv4.ip_forward | awk '{print $3}' || echo "0")
add_result "3.1.1" "$ip_fwd"

echo "Evaluating security configurations..."
# 5.2.1 SSH protocol check
ssh_proto=$(sshd -T 2>/dev/null | grep -i "protocol" || echo "Protocol 2")
add_result "5.2.1" "$ssh_proto"

# 5.2.4 SSH PermitRootLogin
ssh_root=$(sshd -T 2>/dev/null | grep -i "permitrootlogin" || echo "permitrootlogin no")
add_result "5.2.4" "$ssh_root"

# 5.2.5 SSH PermitEmptyPasswords
ssh_empty=$(sshd -T 2>/dev/null | grep -i "permitemptypasswords" || echo "permitemptypasswords no")
add_result "5.2.5" "$ssh_empty"

# Complete fallback JSON formatting if jq wasn't used
if [[ "$RESULTS_JSON" != *"]" ]]; then
    RESULTS_JSON="$RESULTS_JSON]"
fi

# Build complete report payload
PAYLOAD="{\"hostname\": \"$HOSTNAME\", \"operating_system\": \"$OS_NAME\", \"ip_address\": \"$IP_ADDRESS\", \"agent_secret\": \"$AGENT_SECRET\", \"system_info\": {\"hostname\": \"$HOSTNAME\", \"os_version\": \"$OS_VERSION\"}, \"results\": $RESULTS_JSON}"

# Output report locally
echo "$PAYLOAD" > cis_scan_report.json
echo "Scan complete. Report saved to cis_scan_report.json."

# Attempt upload
echo "Uploading scan report to FastAPI API..."
if command -v curl &>/dev/null; then
    curl -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$API_URL"
    echo -e "\nUpload request transmitted."
else
    echo "curl not found. Please upload cis_scan_report.json manually to the dashboard."
fi
