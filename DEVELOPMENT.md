# Information for development

## SSL certificate

### Dummy cert
There is dummy self signed cert only for enable local ssl configuration testing

command that created that cert:
`openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ./dockercompose/website.key -out ./dockercompose/website.crt`