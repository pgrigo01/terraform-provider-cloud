package provider

import (
	"context"
	"fmt"
	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/path"
	"github.com/hashicorp/terraform-plugin-framework/provider"
	"github.com/hashicorp/terraform-plugin-framework/provider/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"os"
	"strings"
)

// Ensure the implementation satisfies the expected interfaces.
var (
	_ provider.Provider = &cloudlabProvider{}
)

// New is a helper function to simplify provider server and testing implementation.
func New(version string) func() provider.Provider {
	return func() provider.Provider {
		return &cloudlabProvider{
			version: version,
		}
	}
}

// cloudlabProvider is the provider implementation.
type cloudlabProvider struct {
	// version is set to the provider version on release, "dev" when the
	// provider is built and ran locally, and "test" when running acceptance
	// testing.
	version string
}

// Metadata returns the provider type name.
func (p *cloudlabProvider) Metadata(_ context.Context, _ provider.MetadataRequest, resp *provider.MetadataResponse) {
	resp.TypeName = "cloudLab"
	resp.Version = p.version
}

// hashicupsProviderModel maps provider schema data to a Go type.
type cloudlabProviderModel struct {
	Credentials_path types.String `tfsdk:"credentials_path"`
	Profile_config   types.Map    `tfsdk:"profile_config"`
}

// Schema defines the provider-level schema for configuration data.
func (p *cloudlabProvider) Schema(_ context.Context, _ provider.SchemaRequest, resp *provider.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"credentials_path": schema.StringAttribute{
				Required:  true,
				Sensitive: true,
			},
			"profile_config": schema.MapAttribute{
				Required:    true,
				ElementType: types.StringType,
			},
		},
	}
}

// Configure prepares a CloudLab API client for data sources and resources.
func (p *cloudlabProvider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
	// Retrieve provider data from configuration
	var config cloudlabProviderModel
	diags := req.Config.Get(ctx, &config)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	// If practitioner provided a configuration value for any of the
	// attributes, it must be a known value.

	profile_aliases := config.Profile_config.Elements()
	needed_profiles := []string{"multi_node"}
	for _, prof := range needed_profiles {
		if profile_aliases[prof] == nil {
			resp.Diagnostics.AddAttributeError(
				path.Root("host"),
				fmt.Sprintf("%s profile uuid not provided", prof),
				fmt.Sprintf("Please provide the %s profile uuid in the provider configuration settings", prof),
			)
		}
	}

	for key := range profile_aliases {
		key_in_needed_profiles := false
		for _, s := range needed_profiles {
			if s == key {
				key_in_needed_profiles = true
				break
			}
		}
		if key_in_needed_profiles == false {
			resp.Diagnostics.AddAttributeError(
				path.Root("host"),
				fmt.Sprintf("%s is not a valid profile config", key),
				"Please provide the correct profile uuid in the provider configuration settings."+
					strings.Join(needed_profiles, ", "),
			)
		}
	}
	if resp.Diagnostics.HasError() {
		return
	}

	if config.Credentials_path.IsUnknown() {
		resp.Diagnostics.AddAttributeError(
			path.Root("host"),
			"Unknown CloudLab credentials (.pem) file",
			"The provider cannot communicate with CloudLab as there is an unknown configuration value for the CloudLab credentials (.pem) file. "+
				"Either target apply the source of the value first, set the value statically in the configuration, or use the CLOUDLAB_CREDENTIALS_PATH environment variable.",
		)
	}

	if resp.Diagnostics.HasError() {
		return
	}

	// Default values to environment variables, but override
	// with Terraform configuration value if set.

	credentials_path := os.Getenv("CLOUDLAB_CREDENTIALS_PATH")

	if !config.Credentials_path.IsNull() {
		credentials_path = config.Credentials_path.ValueString()
	}

	// If any of the expected configurations are missing, return
	// errors with provider-specific guidance.

	if credentials_path == "" {
		resp.Diagnostics.AddAttributeError(
			path.Root("host"),
			"Missing CloudLab credentials (.pem) file",
			"The provider cannot communicate with CloudLab as there is a missing or empty value for the CloudLab credentials (.pem) file. "+
				"Set the host value in the configuration or use the CLOUDLAB_CREDENTIALS_PATH environment variable. "+
				"If either is already set, ensure the value is not empty.",
		)
	}

	if resp.Diagnostics.HasError() {
		return
	}

	// Make the client available during DataSource and Resource
	// type Configure methods.
	client := Client{
		credentialsPath: credentials_path,
	}
	resp.DataSourceData = client
	resp.ResourceData = client
}

// DataSources defines the data sources implemented in the provider.
func (p *cloudlabProvider) DataSources(_ context.Context) []func() datasource.DataSource {
	return nil
}

// Resources defines the resources implemented in the provider.
func (p *cloudlabProvider) Resources(_ context.Context) []func() resource.Resource {
	return []func() resource.Resource{
		CloudLabExperimentResource,
		CloudLabVlanResource,
	}
	return nil
}
