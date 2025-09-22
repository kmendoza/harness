TAG = 0.2.0
PFX = bbquant/consul

build:
	docker build  -t $(PFX):$(TAG)  .

push: build
	docker push $(PFX):$(TAG)

run:
	docker run --rm $(PFX):$(TAG)


#
#
#