

.PHONY: requirements
requirements: requirements/build.sh
	cd requirements && ./build.sh

.PHONY: clean-requirements
clean-requirements:
	$(RM) -r requirements/FPTaylor
	$(RM) -r requirements/gelpia
	$(RM) requirements/log.txt
	$(RM) requirements/debug_eniroment.sh
