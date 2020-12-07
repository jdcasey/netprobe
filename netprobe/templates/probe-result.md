**Timestamp:** {{tstamp|timestamp}}

**Network Speed:** {{speed.ping}}ms ⏳ | {{speed.down_mbps}} ⏬ | {{speed.up_mbps}} ⏫

**Wireless Networks:**
{% for ap in wifi %}↕ `{{ap.chan|rjustify(4)}}` | `{{ap.ssid|cjustify(25)}}` | 📶 `{{ap.str|percent}}`
{% endfor %}
{{wifi|length}} networks detected.

**Ping Results:**
{% for p in ping %}`{{p.host|rjustify(14)}}`: `{{p.min|rjustify(7)}}ms` | `{{p.avg|rjustify(7)}}ms` | `{{p.max|rjustify(7)}}ms` | {{p.loss|percent}}
{% endfor %}
**MTU:** {{MTU.mtu}} bytes (target: {{MTU.target}})
