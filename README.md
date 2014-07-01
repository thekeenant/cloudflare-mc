cloudflare-mc
=============

This script was derived from [wojons/cloudflare-lb](https://github.com/wojons/cloudflare-lb) and [barneygale's ping gist](https://gist.github.com/barneygale/1209061). This acts as a Minecraft proxy load balancer. It will ping a set of IPs repeatedely (configurable interval) and add or remove nodes based on if the IP is accessible to a Minecraft client. Most of the details regarding requirements and configuration options found [here](https://github.com/wojons/cloudflare-lb) apply to this script.

Running
========
$ python cloudflare-mc.py
