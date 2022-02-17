
# Root is mapped to non root in rootless docker 
ABUILD=abuild -F 

prepare: 
	cp -r /aports  /home/builder

fetch:
	( cd /home/builder/aports/main/grep && $(ABUILD) fetch ) 
verify: fetch
	( cd /home/builder/aports/main/grep && $(ABUILD) sanitycheck  ) 
	( cd /home/builder/aports/main/grep && $(ABUILD) verify  ) 
unpack:
	( cd /home/builder/aports/main/grep && $(ABUILD) unpack ) 
patch:
	( cd /home/builder/aports/main/grep && $(ABUILD) prepare ) 
deps:
	( cd /home/builder/aports/main/grep && $(ABUILD) deps ) 
build:
	( cd /home/builder/aports/main/grep && $(ABUILD)  ) 


