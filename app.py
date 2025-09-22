#!/usr/bin/env python3
import os
import subprocess
import sys
import time

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"Stderr: {result.stderr}")
        sys.exit(1)
    return result

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
    print("Dockerfile created successfully")

def build_docker_image():
    """Build the Docker image"""
    run_command("docker build -t ubuntu-ssh .")

def find_available_port(base_port=2222):
    """Find an available port starting from base_port"""
    port = base_port
    max_port = base_port + 100
    
    while port <= max_port:
        try:
            # Check if port is available
            result = subprocess.run(f"netstat -tuln | grep :{port}", 
                                  shell=True, capture_output=True, text=True)
            if result.returncode != 0:  # Port is available
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
    time.sleep(2)
    
    # Check if container is running
    result = run_command("docker ps -f name=ssh-container --format '{{.Status}}'", check=False)
    if "Up" not in result.stdout:
        print("Container failed to start. Checking logs:")
        run_command("docker logs ssh-container", check=False)
        sys.exit(1)
    
    return ssh_port

def test_ssh_connection(port):
    """Test SSH connection to the container"""
    print("Testing SSH connection...")
    
    # Try to connect with SSH
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@localhost -p {port} echo 'SSH connection successful!'"
    result = run_command(ssh_cmd, check=False)
    
    if result.returncode == 0:
        print("✓ SSH connection successful!")
        print(f"Use this command to connect: ssh root@localhost -p {port}")
        print("Password: uditanshu")
    else:
        print("✗ SSH connection failed")
        print("Troubleshooting steps:")
        print("1. Checking container status:")
        run_command("docker ps -a", check=False)
        print("2. Checking container logs:")
        run_command("docker logs ssh-container", check=False)
        print("3. Trying to access container directly:")
        run_command("docker exec -it ssh-container /bin/bash -c 'service ssh status'", check=False)

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
    
    # Test SSH connection
    test_ssh_connection(ssh_port)

if __name__ == "__main__":
    main()
