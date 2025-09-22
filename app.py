#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import socket
import requests

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Stderr: {result.stderr}")
        return result
    return result

def get_public_ip():
    """Get the public IP address"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except:
        return "Unable to determine public IP"

def get_codespaces_url():
    """Get the Codespaces URL if running in GitHub Codespaces"""
    codespace_name = os.environ.get('CODESPACE_NAME')
    if codespace_name:
        return f"https://{codespace_name}.app.github.dev"
    return None

def create_dockerfile():
    """Create the Dockerfile for SSH container"""
    dockerfile_content = '''FROM ubuntu:latest

# Install SSH and necessary packages
RUN apt update -y && \\
    apt install -y openssh-server sudo && \\
    mkdir /var/run/sshd

# Set root password
RUN echo 'root:uditanshu' | chpasswd

# Configure SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \\
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \\
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Expose SSH port
EXPOSE 22

# Start SSH daemon
CMD ["/usr/sbin/sshd", "-D"]
'''
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("✓ Dockerfile created successfully")

def build_docker_image():
    """Build the Docker image"""
    run_command("docker build -t ubuntu-ssh .")

def find_available_port(base_port=2222):
    """Find an available port starting from base_port"""
    port = base_port
    max_port = base_port + 100
    
    while port <= max_port:
        try:
            # Check if port is available using socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result != 0:  # Port is available
                    return port
            port += 1
        except:
            port += 1
    
    return base_port  # Fallback to base port

def run_docker_container():
    """Run the Docker container with SSH"""
    ssh_port = find_available_port()
    
    print(f"Using port {ssh_port} for SSH")
    
    # Run the container
    run_command(f"docker run -d -p {ssh_port}:22 --name ssh-container ubuntu-ssh")
    
    # Wait for SSH to start
    time.sleep(3)
    
    # Check if container is running
    result = run_command("docker ps -f name=ssh-container --format '{{.Status}}'", check=False)
    if "Up" not in result.stdout:
        print("Container failed to start. Checking logs:")
        run_command("docker logs ssh-container", check=False)
        return None
    
    return ssh_port

def test_ssh_connection(port):
    """Test SSH connection to the container"""
    print("Testing SSH connection...")
    
    # Get connection details
    public_ip = get_public_ip()
    codespaces_url = get_codespaces_url()
    
    # Try to connect with SSH
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PasswordAuthentication=yes root@localhost -p {port} echo 'SSH connection successful!'"
    result = run_command(ssh_cmd, check=False)
    
    if result.returncode == 0:
        print("✓ SSH connection successful!")
        print(f"Use this command to connect: ssh root@localhost -p {port}")
        print("Password: uditanshu")
    else:
        print("✗ Direct SSH connection to localhost failed")
        print("This is expected in GitHub Codespaces environment")
    
    # Display connection information for external access
    print("\n📋 Connection Details:")
    if codespaces_url:
        print(f"   Codespaces URL: {codespaces_url}")
    print(f"   Public IP: {public_ip}")
    print(f"   SSH Port: {port}")
    print(f"   Username: root")
    print(f"   Password: uditanshu")
    
    print("\n📝 For Termius or external connection:")
    if codespaces_url:
        print(f"   Host: {codespaces_url.replace('https://', '')}")
    else:
        print(f"   Host: {public_ip}")
    print(f"   Port: {port}")
    print(f"   Username: root")
    print(f"   Password: uditanshu")

def main():
    """Main function"""
    print("Setting up SSH Docker container...")
    
    # Check if Docker is installed
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print("Docker is not installed. Please install Docker first.")
        sys.exit(1)
    
    # Create Dockerfile
    create_dockerfile()
    
    # Build Docker image
    build_docker_image()
    
    # Stop and remove any existing container with the same name
    run_command("docker stop ssh-container 2>/dev/null || true", check=False)
    run_command("docker rm ssh-container 2>/dev/null || true", check=False)
    
    # Run Docker container
    ssh_port = run_docker_container()
    
    if ssh_port:
        # Test SSH connection
        test_ssh_connection(ssh_port)
    else:
        print("Failed to start container. Please check Docker logs.")

if __name__ == "__main__":
    main()
