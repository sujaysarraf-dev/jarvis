import subprocess, time

def ps(cmd):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout + r.stderr

# Open calculator
subprocess.Popen("calc", shell=True)
time.sleep(3)

# Before kill - get all process info
print("=== BEFORE KILL ===")
out = ps('Get-Process CalculatorApp,ApplicationFrameHost -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, MainWindowTitle | Format-Table -AutoSize')
print(out)

# Kill CalculatorApp
print("=== KILLING CalculatorApp ===")
out = ps('Stop-Process -Name CalculatorApp -Force -ErrorAction SilentlyContinue; Write-Host "Done"')
print(out)
time.sleep(2)

# After kill
print("=== AFTER KILL ===")
out = ps('Get-Process CalculatorApp,ApplicationFrameHost -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, MainWindowTitle | Format-Table -AutoSize')
print(out)

# Check if it auto-restarts
time.sleep(1)
print("=== +1s ===")
out = ps('Get-Process CalculatorApp,ApplicationFrameHost -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, MainWindowTitle | Format-Table -AutoSize')
print(out)
