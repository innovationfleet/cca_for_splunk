cca.splunk.ssl-certificates
=========

Role with logic to validate, install and configure SSL certificates for Splunk processes. Certificates are split into 4 categories to match the Splunk configuration options. These certificates are deployed to all servers depending on what services that should be made available. To validate correctly on the Web and via rest all certificates need to be SAN certificates.

## Server Certificates
Used by the Splunkd process for REST actions and general S2S communication.

## Inputs Certificate
Used on index server and other instances that are configured to receive S2S data.

## Outputs Certificate
Used on all Splunk instances that sends data via S2S that has SSL enabled on their input.

## Web Certificate
Used on all Splunk Web UI's where https is enabled.

Requirements
------------

5 different certificates needs to be available in splunk/etc/auth/certs/ in the Splunk infrastructure repo on the CCA manager server.

### Root CA certificate
Combined certificate file with any intermediate signing certificate in correct order ending with the Root CA certificate.

## Server Certificates
Certificate with all SAN's required in the environment, stored alongside the encrypted key. Name of certificates and key needs to match `cca_splunk_extension_server_cert` and `cca_splunk_extension_server_key` variables found in `environments/ENVIRONMENT_NAME/group_vars/all/env_specific` file.

## Inputs Certificate
Certificate with all SAN's required in the environment, stored alongside the encrypted key. Name of certificates and key needs to match `cca_splunk_extension_inputs_cert` and `cca_splunk_extension_inputs_key` variables found in `environments/ENVIRONMENT_NAME/group_vars/all/env_specific` file.

## Outputs Certificate
Certificate with all SAN's required in the environment, stored alongside the encrypted key. Name of certificates and key needs to match `cca_splunk_extension_outputs_cert` and `cca_splunk_extension_outputs_key` variables found in `environments/ENVIRONMENT_NAME/group_vars/all/env_specific` file.

## Web Certificate
Certificate with all SAN's required in the environment, stored alongside the encrypted key. Name of certificates and key needs to match `cca_splunk_extension_web_cert` and `cca_splunk_extension_web_key` variables found in `environments/ENVIRONMENT_NAME/group_vars/all/env_specific` file.

Role Variables
--------------

Description


### group_vars/all/cca_splunk_secrets
* `cca_splunk_certs_server_sslpassword_hash`
  * Hashed value of sslpassword based on the common splunk.secret that must match between Splunk instances.
* `cca_splunk_certs_server_sslpassword`
  * Clear text sslpassword stored in as ansible vault
* `cca_splunk_certs_server_default_sslpassword_hash`
  * Hashed value of sslpassword based on the common splunk.secret that must match between Splunk instances.
* `cca_splunk_certs_server_default_sslpassword`
  * Clear text sslpassword stored in as ansible vault
* `cca_splunk_certs_inputs_sslpassword_hash`
  * Hashed value of sslpassword based on the common splunk.secret that must match between Splunk instances.
* `cca_splunk_certs_inputs_sslpassword`
  * Clear text sslpassword stored in as ansible vault
* `cca_splunk_certs_outputs_sslpassword_hash`
  * Hashed value of sslpassword based on the common splunk.secret that must match between Splunk instances.
* `cca_splunk_certs_outputs_sslpassword`
  * Clear text sslpassword stored in as ansible vault
* `cca_splunk_certs_web_sslpassword_hash`
  * Hashed value of sslpassword based on the common splunk.secret that must match between Splunk instances.
* `cca_splunk_certs_web_sslpassword`
  * Clear text sslpassword stored in as ansible vault

### group_vars/all/env_specific
* `cca_splunk_cert_enrollment_method`
  * Specify if certs are enrolled with selfsigned certificates or manually created ones.
* `cca_splunk_extension_certs_path`
  Path to where the certificate and private keys are store on manager server
* `cca_splunk_extension_cert_rootca`
  * Filename of Root CA certificate. Name the certificate with its valid dates for both CA and Intermediate CA's, for example Innovationfleet_CA1_20291111_Issuing_CA1_2024111.pem
* `cca_splunk_extension_server_cert`
  * Filename of server certificate. Name the certificate with its valid date, for example splunk-server_20231210.cer. It makes it clear when the certs has to be renewed and.
* `cca_splunk_extension_server_key`
  * Give the corresponding private key the same date, for example splunk-server_20231210.key as they are related and should be replaced when renewing the certificates.
* `cca_splunk_extension_inputs_cert`
  * Filename of server certificate. Name the certificate with its valid date, for example splunk-inputs_20231210.cer. It makes it clear when the certs has to be renewed and.
* `cca_splunk_extension_inputs_key`
  * Give the corresponding private key the same date, for example splunk-inputs_20231210.key as they are related and should be replaced when renewing the certificates.
* `cca_splunk_extension_outputs_cert`
  * Filename of server certificate. Name the certificate with its valid date, for example splunk-outputs_20231210.cer. It makes it clear when the certs has to be renewed and.
* `cca_splunk_extension_outputs_key`
  * Give the corresponding private key the same date, for example splunk-outputs_20231210.key as they are related and should be replaced when renewing the certificates.
* `cca_splunk_extension_web_cert`
  * Filename of server certificate. Name the certificate with its valid date, for example splunk-web_20231210.cer. It makes it clear when the certs has to be renewed and.
* `cca_splunk_extension_web_key`
  * Give the corresponding private key the same date, for example splunk-web_20231210.key as they are related and should be replaced when renewing the certificates.

### group_vars/all/cca_splunk_settings
* `cca_splunk_cert_prefix`
  * Set to splunk
* `cca_splunk_certs_relative_path`
  * `etc/auth` if selfsigned is used as cert enrollment method, else it's set to `etc/auth/certs`
* `cca_splunk_certs_path`
  * `splunk_path`/`cca_splunk_certs_relative_path`
* `cca_splunk_certs_staging_path`
  * Sets to full staging path
* `cca_splunk_certs_home_path`
  * Sets to relative $SPLUNK_HOME staging path
* `cca_splunk_certs_inputs_cert`
  * Set to server.pem if selfsigned is used as cert enrollment method, else it's set to splunk-inputs.cer
* `cca_splunk_certs_inputs_key`
  * Set to server.key if selfsigned is used as cert enrollment method, else it's set to splunk-inputs.key
* `cca_splunk_certs_inputs_staging_cert`
  * Sets to the value of `cca_splunk_extension_inputs_cert` if defined else `cca_splunk_cert_prefix`-inputs.cer
* `cca_splunk_certs_inputs_staging_key`
  * Sets to the value of `cca_splunk_extension_inputs_key` if defined else `cca_splunk_cert_prefix`-inputs.key
* `cca_splunk_certs_outputs_cert`
  * Set to server.pem if selfsigned is used as cert enrollment method, else it's set to splunk-inputs.cer
* `cca_splunk_certs_outputs_key`
  * Set to server.key if selfsigned is used as cert enrollment method, else it's set to splunk-outputs.key
* `cca_splunk_certs_outputs_staging_cert`
  * Sets to the value of `cca_splunk_extension_outputs_cert` if defined else `cca_splunk_cert_prefix`-outputs.cer
* `cca_splunk_certs_outputs_staging_key`
  * Sets to the value of `cca_splunk_extension_outputs_key` if defined else `cca_splunk_cert_prefix`-outputs.key
* `cca_splunk_certs_server_cert`
  * Set to server.pem if selfsigned is used as cert enrollment method, else it's set to splunk-server.cer
* `cca_splunk_certs_server_key`
  * Set to server.key if selfsigned is used as cert enrollment method, else it's set to splunk-server.key
* `cca_splunk_certs_server_staging_cert`
  * Sets to the value of `cca_splunk_extension_server_cert` if defined else `cca_splunk_cert_prefix`-server.cer
* `cca_splunk_certs_server_staging_key`
  * Sets to the value of `cca_splunk_extension_server_key` if defined else `cca_splunk_cert_prefix`-server.key
* `cca_splunk_certs_web_cert`
  * Set to the splunkweb/cert.pem if selfsigned is used as cert enrollment method, else it's set to splunk-web.cer
* `cca_splunk_certs_web_key`
  * Set to splunkweb/privkey.pem if selfsigned is used as cert enrollment method, else it's set to splunk-server.key
* `cca_splunk_certs_web_staging_cert`
  * Sets to the value of `cca_splunk_extension_server_cert` if defined else `cca_splunk_cert_prefix`-server.cer
* `cca_splunk_certs_web_staging_key`
  * Sets to the value of `cca_splunk_extension_web_key` if defined else `cca_splunk_cert_prefix`-web.key


Tasks
------------

### Main

### Standalone tasks
* `deploy_manual_certs.yml`
  * Deploy certificates and validate matching private keys
* `inputs_certificate.yml`
  * Set facts for input certificate variables
* `outputs_certificate.yml`
  * Set facts for output certificate variables
* `server_certificate.yml`
  * Set facts for server certificate variables
* `validate_manual_certificates.yml`
  * Validates if certificate is available and valid, checks all 4 certificates.
    Compares checksums of certificates stored on Manager server and on Splunk server.
    If the file doesn't exists or match each other it will trigger the `deploy_manual_certs.yml`
    task under the condition that `cca_splunk_cert_enrollment_method` is set to manual.
* `web_certificate.yml`
  * Set facts for web certificate variables

Dependencies
------------

None

License
-------

MIT