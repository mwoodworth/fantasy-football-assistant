#!/usr/bin/env python3
"""
Start the Fantasy Football Assistant with WebSocket support
Checks all dependencies before starting
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def check_python_dependencies():
    """Check if all Python dependencies are installed"""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'python-socketio',
        'websockets',
        'sqlalchemy',
        'httpx',
        'python-jose',
        'passlib',
        'pandas',
        'numpy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing Python packages: {', '.join(missing)}")
        print("📦 Installing missing packages...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
        print("✅ Python dependencies installed")
    else:
        print("✅ All Python dependencies are installed")

def check_frontend_dependencies():
    """Check if all frontend dependencies are installed"""
    print("\n🔍 Checking frontend dependencies...")
    
    frontend_dir = Path(__file__).parent.parent / "frontend"
    package_json = frontend_dir / "package.json"
    node_modules = frontend_dir / "node_modules"
    
    if not package_json.exists():
        print("❌ package.json not found in frontend directory")
        return False
    
    # Check if node_modules exists
    if not node_modules.exists():
        print("📦 node_modules not found. Running npm install...")
        install_frontend_deps(frontend_dir)
        return True
    
    # Check specific critical packages
    with open(package_json, 'r') as f:
        package_data = json.load(f)
    
    required_packages = [
        'react',
        'react-dom',
        '@tanstack/react-query',
        'axios',
        'socket.io-client',  # Critical for WebSocket
        'lucide-react',
        'tailwindcss'
    ]
    
    dependencies = package_data.get('dependencies', {})
    missing = []
    
    for pkg in required_packages:
        if pkg in dependencies:
            pkg_path = node_modules / pkg
            if not pkg_path.exists():
                missing.append(pkg)
    
    if missing:
        print(f"❌ Missing frontend packages: {', '.join(missing)}")
        print("📦 Running npm install to fix missing packages...")
        install_frontend_deps(frontend_dir)
    else:
        print("✅ All frontend dependencies are installed")
    
    return True

def install_frontend_deps(frontend_dir):
    """Install frontend dependencies"""
    try:
        # First try regular npm install
        result = subprocess.run(
            ["npm", "install"],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("⚠️  npm install failed, trying with --force...")
            # If it fails due to permissions, try with force
            result = subprocess.run(
                ["npm", "install", "--force"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ npm install failed: {result.stderr}")
                print("\n🔧 To fix npm permissions, run:")
                print("  sudo chown -R $(whoami) ~/.npm")
                print("  Then run this script again")
                return False
        
        print("✅ Frontend dependencies installed")
        return True
        
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js and npm")
        return False

def check_espn_service():
    """Check if ESPN service dependencies are installed"""
    print("\n🔍 Checking ESPN service dependencies...")
    
    espn_dir = Path(__file__).parent.parent / "espn-service"
    package_json = espn_dir / "package.json"
    node_modules = espn_dir / "node_modules"
    
    if not package_json.exists():
        print("⚠️  ESPN service not found (optional)")
        return True
    
    if not node_modules.exists():
        print("📦 Installing ESPN service dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=espn_dir, check=True)
            print("✅ ESPN service dependencies installed")
        except Exception as e:
            print(f"⚠️  ESPN service setup failed (optional): {e}")
    else:
        print("✅ ESPN service dependencies are installed")
    
    return True

def start_services():
    """Start the backend and frontend services"""
    print("\n🚀 Starting services...")
    
    # Start backend
    print("🔧 Starting backend server with WebSocket support...")
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.main:app",
        "--host", "0.0.0.0",
        "--port", "6001",
        "--reload"
    ]
    
    # Start frontend
    print("🎨 Starting frontend development server...")
    frontend_dir = Path(__file__).parent.parent / "frontend"
    frontend_cmd = ["npm", "run", "dev"]
    
    try:
        # Start backend in background
        backend_process = subprocess.Popen(backend_cmd)
        print("✅ Backend started on http://localhost:6001")
        print("   - REST API: http://localhost:6001/api")
        print("   - WebSocket: ws://localhost:6001/socket.io")
        print("   - API Docs: http://localhost:6001/api/docs")
        
        # Start frontend
        frontend_process = subprocess.Popen(frontend_cmd, cwd=frontend_dir)
        print("✅ Frontend starting on http://localhost:5173")
        
        print("\n📡 WebSocket features:")
        print("   - Real-time draft updates")
        print("   - Instant pick notifications")
        print("   - Live sync status indicator")
        
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Wait for processes
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Services stopped")
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    print("🏈 Fantasy Football Assistant - WebSocket Edition")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check dependencies
    check_python_dependencies()
    
    if not check_frontend_dependencies():
        print("\n❌ Frontend dependency check failed")
        print("Please fix the issues above and try again")
        sys.exit(1)
    
    check_espn_service()
    
    # Re-enable WebSocket in frontend if it was disabled
    print("\n🔧 Enabling WebSocket support in frontend...")
    enable_websocket_in_frontend()
    
    # Start services
    start_services()

def enable_websocket_in_frontend():
    """Re-enable WebSocket code if it was commented out"""
    tracker_file = Path(__file__).parent.parent / "frontend/src/components/draft/DraftLiveTracker.tsx"
    
    if tracker_file.exists():
        content = tracker_file.read_text()
        
        # Check if WebSocket is disabled
        if "// import { useWebSocket }" in content or "/*\n  const { isConnected } = useWebSocket" in content:
            print("🔧 Re-enabling WebSocket in DraftLiveTracker...")
            
            # Re-enable import
            content = content.replace(
                "// import { useWebSocket } from '../../hooks/useWebSocket' // Temporarily disabled until socket.io-client is installed",
                "import { useWebSocket } from '../../hooks/useWebSocket'"
            )
            
            # Re-enable WebSocket hook usage
            content = content.replace(
                """  // WebSocket connection for real-time updates
  // Temporarily disabled until socket.io-client is installed
  const isConnected = false
  /*
  const { isConnected } = useWebSocket({""",
                """  // WebSocket connection for real-time updates
  const { isConnected } = useWebSocket({"""
            )
            
            content = content.replace(
                """  })
  */""",
                """  })"""
            )
            
            # Update polling interval
            content = content.replace(
                "refetchInterval: 5000, // Poll every 5 seconds (WebSocket temporarily disabled)",
                "refetchInterval: 30000, // Reduced polling to 30s as WebSocket is primary"
            )
            
            tracker_file.write_text(content)
            print("✅ WebSocket re-enabled in frontend")

if __name__ == "__main__":
    main()