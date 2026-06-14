# https://hub.docker.com/_/python
FROM python:3.14.6-bookworm
RUN apt update && apt upgrade -y

# https://trivy.dev/docs/latest/getting-started/installation/#install-script-official
RUN apt install wget gnupg
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | tee /usr/share/keyrings/trivy.gpg > /dev/null
RUN echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | tee -a /etc/apt/sources.list.d/trivy.list
RUN apt update
RUN apt install trivy

WORKDIR /security_scanner
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod a+x ./scripts/run-security-scanner.sh

ENTRYPOINT ["/bin/sh", "./scripts/run-security-scanner.sh"]
