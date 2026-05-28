#!/bin/bash
echo "Backing up /etc/hosts to /etc/hosts.bak..."
cp /etc/hosts /etc/hosts.bak

echo "Rebuilding /etc/hosts with correct formatting..."
cat > /etc/hosts << 'EOF'
##
# Host Database
#
# localhost is used to configure the loopback interface
# when the system is booting.  Do not change this entry.
##
127.0.0.1       localhost
255.255.255.255 broadcasthost
::1             localhost

185.25.23.140   barkas-n-i.gr
185.25.23.140   delta-marine.gr

# Added by Docker Desktop
# To allow the same kube context to work on the host and the container:
127.0.0.1       kubernetes.docker.internal
# End of section

# BEGIN SELFCONTROL BLOCK
0.0.0.0 x18r.com
::      x18r.com
0.0.0.0 www.jable.tv
::      www.jable.tv
0.0.0.0 jable.tv
::      jable.tv
0.0.0.0 www.jav.guru
::      www.jav.guru
0.0.0.0 missav.com
::      missav.com
0.0.0.0 www.sayhentai.one
::      www.sayhentai.one
0.0.0.0 stripchat.com
::      stripchat.com
0.0.0.0 www.missav.com
::      www.missav.com
0.0.0.0 sayhentai.one
::      sayhentai.one
0.0.0.0 www.stripchat.com
::      www.stripchat.com
0.0.0.0 www.x18r.com
::      www.x18r.com
0.0.0.0 jav.guru
::      jav.guru
# END SELFCONTROL BLOCK
EOF

echo "Done! The /etc/hosts file has been fixed."
