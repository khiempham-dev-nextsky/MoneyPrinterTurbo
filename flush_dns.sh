#!/bin/bash
echo "Flushing macOS DNS cache..."
dscacheutil -flushcache
killall -HUP mDNSResponder
echo "DNS cache flushed successfully!"
