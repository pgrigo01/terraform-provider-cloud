package provider

import (
	"context"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
)

// Ensure the implementation satisfies the expected interfaces.
var (
	_ resource.Resource = &cloudlabVlanResource{}
)

// cloudlabVlanResource is a helper function to simplify the provider implementation.
func CloudLabVlanResource() resource.Resource {
	return &cloudlabVlanResource{}
}

// cloudlabVlanResource is the resource implementation.
type cloudlabVlanResource struct{}

// Metadata returns the resource type name.
func (r *cloudlabVlanResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = "cloudlab_vlan"
}

// orderResourceModel maps the resource schema data.
type cloudlabVlanModel struct {
	Name        types.String `tfsdk:"name"`
	Subnet_mask types.String `tfsdk:"subnet_mask"`
}

// Schema defines the schema for the resource.
func (r *cloudlabVlanResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"name": schema.StringAttribute{
				Required: true,
			},
			"subnet_mask": schema.StringAttribute{
				Required: true,
			},
		},
	}
}

// Create creates the resource and sets the initial Terraform state.
func (r *cloudlabVlanResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	// Retrieve values from plan
	var plan cloudlabVlanModel
	diags := req.Plan.Get(ctx, &plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Set state to fully populated data
	diags = resp.State.Set(ctx, plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
}

// Read refreshes the Terraform state with the latest data.
func (r *cloudlabVlanResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
}

// Update updates the resource and sets the updated Terraform state on success.
func (r *cloudlabVlanResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
}

// Delete deletes the resource and removes the Terraform state on success.
func (r *cloudlabVlanResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
}
