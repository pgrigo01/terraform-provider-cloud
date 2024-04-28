package provider

var AGGREGATELIST = [][]string{
	{"urn:publicid:IDN+emulab.net+authority+cm", "emulab.net"},
	{"urn:publicid:IDN+utah.cloudlab.us+authority+cm", "utah.cloudlab.us"},
	{"urn:publicid:IDN+clemson.cloudlab.us+authority+cm", "clemson.cloudlab.us"},
	{"urn:publicid:IDN+wisc.cloudlab.us+authority+cm", "wisc.cloudlab.us"},
	{"urn:publicid:IDN+apt.emulab.net+authority+cm", "apt.emulab.net"},
	{"", "Any"},
}

var IMAGELIST = [][]string{
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD", "UBUNTU 18.04"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD", "UBUNTU 16.04"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD", "UBUNTU 20.04"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD", "CENTOS 7"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//FBSD113-64-STD", "FreeBSD 11.3"},
}

func GetImageListChoices() []string {
	var imageChoices []string
	for _, tuple := range IMAGELIST {
		imageChoices = append(imageChoices, tuple[1])
	}
	return imageChoices
}

func GetAggregateListChoices() []string {
	var aggregateChoices []string
	for _, tuple := range AGGREGATELIST {
		aggregateChoices = append(aggregateChoices, tuple[1])
	}
	return aggregateChoices
}

func AddImageParam(m *map[string]string, image string) {
	for _, tuple := range IMAGELIST {
		if tuple[1] == image {
			(*m)["image"] = tuple[0]
		}
	}
}

func AddAggregateParam(m *map[string]string, aggregate string) {
	for _, tuple := range AGGREGATELIST {
		if tuple[1] == aggregate {
			(*m)["aggregate"] = tuple[0]
		}
	}
}
