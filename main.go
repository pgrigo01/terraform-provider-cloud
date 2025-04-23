// Copyright (c) HashiCorp, Inc.
// SPDX-License-Identifier: MPL-2.0

package main

import (
	"context"
	"flag"
	"log"

	"github.com/hashicorp/terraform-plugin-framework/providerserver"

	"terraform-provider-cloudlab/internal/provider"
)

// Run "go generate" to format example Terraform files if Terraform is installed.
//go:generate terraform fmt -recursive ./examples/

// Build the provider binary so tfplugindocs can read its schema.
//go:generate go build -o terraform-provider-cloudlab

// Generate docs using the older-style tfplugindocs flags.
// (Your installed version does not support --dir or --provider.)
//   -provider-dir=.           : Tells tfplugindocs to look for provider code in the current directory.
//   -provider-name=cloudlab   : The logical name of your provider in Terraform configs.
//   -rendered-provider-name=cloudlab : The name to display in generated docs.
//
// You can add other flags (e.g. -examples-dir, -rendered-website-dir) if desired.
//
// Note: If you need to pass a specific Terraform version or skip building the provider,
// check the usage text you saw in the error to find the appropriate flags.
//
//go:generate go run github.com/hashicorp/terraform-plugin-docs/cmd/tfplugindocs -provider-dir=. -provider-name=cloudlab -rendered-provider-name=cloudlab

var (
	// These will be set by the goreleaser configuration
	// to appropriate values for the compiled binary.
	version string = "dev"
)

func main() {
	var debug bool

	flag.BoolVar(&debug, "debug", false, "set to true to run the provider with support for debuggers like delve")
	flag.Parse()

	opts := providerserver.ServeOpts{
		// NOTE: This is not a typical Terraform Registry provider address,
		// such as registry.terraform.io/hashicorp/cloudlab. This specific
		// provider address is used in these tutorials in conjunction with a
		// specific Terraform CLI configuration for manual development testing
		// of this provider.
		Address: "hashicorp.com/edu/cloudlab",
		Debug:   debug,
	}

	err := providerserver.Serve(context.Background(), provider.New(version), opts)
	if err != nil {
		log.Fatal(err.Error())
	}
}
