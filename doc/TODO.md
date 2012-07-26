TODO
====

Remarks/TODO :
- need to clean old code + dns server code (remove endswith from lib/dnsServer/namecoindns.py, etc)
- finish the split between the DNS service and namespaces plugins
* plugins
- DATA: allow to start and stop namecoin to do full updates
- DATA: fetch data only for used namespaces
- create plugins for names (auto-renew, register in one step), domains (creation) and aliases (creation)
- cronjob to update dynamic DNS
- update OS configuration at start
* other
- tested only on linux => need to be adapted for windows & mac too
- need a gui


