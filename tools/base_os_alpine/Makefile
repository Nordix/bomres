
include build/config/settings


prepare:
	@make -C build  builder


ext_build:
	@make -C build  public_build 

int_build:
	@make -C build  download 
	@make -C build  private_build 

test:
	@make -C test   test 


build: clean prepare ext_build int_build  test 

clean:
	@make -C build clean
	@make -C test clean
	@make -C deploy clean

.PHONY: build
.PHONY: test
.PHONY: deploy
