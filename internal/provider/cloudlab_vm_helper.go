package provider

import (
	"context"
	"fmt"

	"github.com/hashicorp/terraform-plugin-log/tflog"
)

var AGGREGATELIST = [][]string{
	{"urn:publicid:IDN+emulab.net+authority+cm", "emulab.net"},
	{"urn:publicid:IDN+utah.cloudlab.us+authority+cm", "utah.cloudlab.us"},
	{"urn:publicid:IDN+clemson.cloudlab.us+authority+cm", "clemson.cloudlab.us"},
	{"urn:publicid:IDN+wisc.cloudlab.us+authority+cm", "wisc.cloudlab.us"},
	{"urn:publicid:IDN+apt.emulab.net+authority+cm", "apt.emulab.net"},
	{"", "Any"},
}

var IMAGELIST = [][]string{
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD", "UBUNTU 20.04"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD", "UBUNTU 22.04"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-STD", "UBUNTU 24.04"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD", "CENTOS 7"},
	{"urn:publicid:IDN+emulab.net+image+emulab-ops//FBSD113-64-STD", "FreeBSD 11.3"},
}

// Return only the friendly names for use in Terraform validators
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

// AddImageParam tries to match the friendly name (e.g., "UBUNTU 20.04") to the actual URN.
func AddImageParam(ctx context.Context, m *map[string]string, image string) {
	matched := false
	for _, tuple := range IMAGELIST {
		if tuple[1] == image {
			(*m)["image"] = tuple[0]
			matched = true
			tflog.Info(ctx, fmt.Sprintf("[AddImageParam] Matched image=%q -> URN=%q", image, tuple[0]))
			break
		}
	}
	if !matched {
		tflog.Warn(ctx, fmt.Sprintf("[AddImageParam] Could not match image=%q to any known URN!", image))
	}
}

// AddAggregateParam tries to match the friendly name (e.g., "Any") to the actual URN.
func AddAggregateParam(ctx context.Context, m *map[string]string, aggregate string) {
	matched := false
	for _, tuple := range AGGREGATELIST {
		if tuple[1] == aggregate {
			(*m)["aggregate"] = tuple[0]
			matched = true
			tflog.Info(ctx, fmt.Sprintf("[AddAggregateParam] Matched aggregate=%q -> URN=%q", aggregate, tuple[0]))
			break
		}
	}
	if !matched {
		tflog.Warn(ctx, fmt.Sprintf("[AddAggregateParam] Could not match aggregate=%q to any known URN!", aggregate))
	}
}
