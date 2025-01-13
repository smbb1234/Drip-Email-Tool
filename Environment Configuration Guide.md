# Environment Configuration Guide

## Prerequisites
Ensure the following before proceeding:
- A system running Linux (preferably Ubuntu) or another OS that supports Docker.
- Sudo or root user access.

---

## Step 1: Install Docker Using `test-docker.sh`

### 1. Update the System
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Download the Installation Script
```bash
curl -fsSL https://get.docker.com -o test-docker.sh
```

### 3. Run the Script to Install Docker
```bash
sudo sh test-docker.sh
```

### 4. Verify Installation
```bash
docker --version
```

You should see the Docker version printed.

---

## Step 2: Install Docker Compose

### 1. Download the Docker Compose Binary
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K[^"]+')/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

### 2. Apply Execute Permissions
```bash
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Verify Installation
```bash
docker-compose --version
```
You should see the Docker Compose version printed.

---

## Step 3: Deploy an Nginx Container

### 1. Pull the Official Nginx Image
```bash
sudo docker pull nginx
```

### 2. Run the Nginx Container
```bash
sudo docker run -d --name nginx -p 80:80 nginx
```
- `-d`: Run the container in detached mode.
- `--name nginx`: Assign the name `nginx` to the container.
- `-p 80:80`: Map port 80 of the container to port 80 on the host.

### 3. Verify the Container is Running
```bash
docker ps
```
This command lists all running containers. You should see the `nginx` container listed.

### 4. Test Nginx
Open a web browser and navigate to `http://localhost`. You should see the Nginx welcome page.

---

## Step 4: Optional Configuration

### 1. Create Local Directories for Nginx
```bash
mkdir -p ~/docker/nginx/conf ~/docker/nginx/logs ~/docker/nginx/www
```

### 2. Copy the Default Configuration File
```bash
docker cp nginx:/etc/nginx/nginx.conf ~/docker/nginx/conf/nginx.conf
```

### 3. Stop and Remove the Running Container
```bash
sudo docker stop nginx

sudo docker rm nginx
```

### 4. Re-run Nginx with Mounted Directories
```bash
sudo docker run -d --name nginx -p 8080:8080 \
-v ~/docker/nginx/conf/nginx.conf:/etc/nginx/nginx.conf \
-v ~/docker/nginx/www:/usr/share/nginx/html \
-v ~/docker/nginx/logs:/var/log/nginx nginx \
--add-host=host.docker.internal:host-gateway \
nginx
```
This allows you to:
- Customize the configuration file.
- Serve your own content from the `www` directory.
- View logs in the `logs` directory.
- Use `--add-host=host.docker.internal:host-gatewa`y to enable containers to resolve `host.docker.internal` to the host machine’s gateway. This is useful for accessing services running on the host directly from within the container.

---

### Optional: Deploy Portainer for Docker Management
Portainer is a lightweight management UI for Docker.

### 1. Pull the Portainer Image
```bash
sudo docker pull portainer/portainer-ce

```

### 2. Create a Volume for Portainer Data
```bash
sudo docker volume create portainer_data
```

### 3. Run the Portainer Container
```bash
sudo docker run -d --name portainer -p 9000:9000 \
--restart=always \
-v /var/run/docker.sock:/var/run/docker.sock \
-v portainer_data:/data portainer/portainer-ce
```
- `-d`: Run the container in detached mode.
- `--name` portainer: Assign the name `portainer` to the container.
- `-p 9000:900`0: Map port 9000 of the container to port 9000 on the host.
- `--restart=alway`s: Ensure the container restarts automatically if it stops.
- `-v`: Bind mount the Docker socket and Portainer data volume.


### 4. Access Portainer
Open a web browser and navigate to `http://localhost:9000`. Follow the on-screen instructions to complete the setup.
username: `admin`
password: `revolve12345`

---

## Additional Commands

### Stop the Nginx Container
```bash
sudo docker stop nginx
```

### Restart the Nginx Container
```bash
sudo docker start nginx
```

### Remove the Nginx Container
```bash
sudo docker rm nginx
```

---

## Additional Information: Adding Environment Variables

### On Ubuntu

#### Temporary Environment Variables
To set a temporary environment variable, use the `export` command. This variable will only last for the current terminal session:
```bash
export VARIABLE_NAME="value"
```
For example:
```bash
export MY_VAR="Hello, Ubuntu!"
```
Verify it with:
```bash
echo $MY_VAR
```

#### Permanent Environment Variables
To make an environment variable permanent, add it to the `~/.bashrc` file (for a single user):
```bash
echo 'export VARIABLE_NAME="value"' >> ~/.bashrc
```
Apply the changes with:
```bash
source ~/.bashrc
```
For system-wide variables, add them to `/etc/environment` (do not use `export` in this file):
```bash
sudo vim /etc/environment
```
Add the variable:
```bash
VARIABLE_NAME="value"
```
Save the file and log out or reboot for changes to take effect.

### On Windows

#### Temporary Environment Variables

#### In PowerShell
To set a temporary environment variable in PowerShell, use:
```powershell
$env:VARIABLE_NAME="value"
```
For example:
```powershell
$env:MY_VAR="Hello, Windows!"
```
This variable will only exist in the current PowerShell session.

#### In Command Prompt (CMD)
To set a temporary environment variable in CMD, use the `set` command:
```cmd
set VARIABLE_NAME=value
```
For example:
```cmd
set MY_VAR=Hello, Windows!
```
This variable will only exist in the current CMD session.

#### Permanent Environment Variables
To set a permanent environment variable:
1. Open the Start menu and search for "Environment Variables".
2. Click on "Edit the system environment variables".
3. In the "System Properties" window, click on the "Environment Variables" button.
4. Add a new variable under "User variables" or "System variables".
5. Provide the variable name and value, and click "OK".

Alternatively, use PowerShell:
```powershell
[System.Environment]::SetEnvironmentVariable("VARIABLE_NAME", "value", [System.EnvironmentVariableTarget]::User)
```
For system-wide variables:
```powershell
[System.Environment]::SetEnvironmentVariable("VARIABLE_NAME", "value", [System.EnvironmentVariableTarget]::Machine)
```

---