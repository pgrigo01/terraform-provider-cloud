package provider

import (
	"context"
	"fmt"
	"github.com/hashicorp/terraform-plugin-framework-validators/stringvalidator"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/schema/validator"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
	"strings"
)

// Ensure the implementation satisfies the expected interfaces.
var (
	_ resource.Resource = &cloudlabvmResource{}
)

// CloudLabExperimentResource is a helper function to simplify the provider implementation.
func CloudLabExperimentResource() resource.Resource {
	return &cloudlabvmResource{}
}

// cloudlabvmResource is the resource implementation.
type cloudlabvmResource struct {
	client Client
}

// Metadata returns the resource type name.
func (r *cloudlabvmResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = "cloudlab_vm"
}

// cloudlabvmResourceModel maps the resource schema data.
type cloudlabvmModel struct {
	Uuid        types.String        `tfsdk:"uuid"`
	Name        types.String        `tfsdk:"name"`
	Aggregate   types.String        `tfsdk:"aggregate"`
	Image       types.String        `tfsdk:"image"`
	Routable_ip types.Bool          `tfsdk:"routable_ip"`
	Vlans       []cloudlabVlanModel `tfsdk:"vlans"`
}

// Schema defines the schema for the resource.
func (r *cloudlabvmResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"uuid": schema.StringAttribute{
				Computed: true,
			},
			"name": schema.StringAttribute{
				Required: true,
			},
			"aggregate": schema.StringAttribute{
				Required: true,
				Validators: []validator.String{
					stringvalidator.OneOf(GetAggregateListChoices()...),
				},
			},
			"image": schema.StringAttribute{
				Required: true,
				Validators: []validator.String{
					stringvalidator.OneOf(GetImageListChoices()...),
				},
			},
			"routable_ip": schema.BoolAttribute{
				Required: true,
			},
			"vlans": schema.ListNestedAttribute{
				Optional: true,
				NestedObject: schema.NestedAttributeObject{
					Attributes: map[string]schema.Attribute{
						"name": schema.StringAttribute{
							Required: true,
						},
						"subnet_mask": schema.StringAttribute{
							Required: true,
						},
					},
				},
			},
		},
	}
}

func (r *cloudlabvmResource) Configure(ctx context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
	// Prevent panic if the provider has not been configured.
	if req.ProviderData == nil {
		return
	}

	client, ok := req.ProviderData.(Client)

	if !ok {
		resp.Diagnostics.AddError(
			"Unexpected Resource Configure Type",
			fmt.Sprintf("Expected *provider.Client, got: %T. Please report this issue to the provider developers.", req.ProviderData),
		)

		return
	}

	r.client = client
}

// Create creates the resource and sets the initial Terraform state.
func (r *cloudlabvmResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	// Retrieve values from plan
	var plan cloudlabvmModel
	diags := req.Plan.Get(ctx, &plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	sharedvlans := func() string {
		var vlans []map[string]string
		for _, vlan := range plan.Vlans {
			vlans = append(vlans, map[string]string{
				"name":        strings.Replace(vlan.Name.String(), "\"", "", -1),
				"subnet_mask": strings.Replace(vlan.Subnet_mask.String(), "\"", "", -1),
			})
		}
		vlansJson, err := mapToJSON(vlans)
		if err != nil {
			resp.Diagnostics.AddError(
				"Error converting to json",
				"Error converting to json: "+err.Error(),
			)
			return ""
		}
		return vlansJson
	}()

	tflog.Info(ctx, sharedvlans)

	if resp.Diagnostics.HasError() {
		return
	}

	params := map[string]string{
		"name":        plan.Name.String(),
		"routable_ip": plan.Routable_ip.String(),
	}
	AddImageParam(&params, plan.Image.String())
	AddAggregateParam(&params, plan.Aggregate.String())
	if len(plan.Vlans) != 0 {
		params["sharedVlans"] = sharedvlans
	}

	_, err := r.client.startExperiment(params)

	if err != nil {
		resp.Diagnostics.AddError(
			"Error creating vm",
			"Could not create vm, unexpected error: "+err.Error(),
		)
		return
	}

	response, status, err := r.client.experimentStatus(plan.Name.String())
	if err != nil {
		resp.Diagnostics.AddError(
			"Error reading vm status",
			"Could not read vm status, unexpected error: "+err.Error(),
		)
		return
	}
	if status == EXPERIMENT_NOT_EXISTS {
		resp.Diagnostics.AddError(
			"Error reading vm status",
			"vm status not exists, unexpected error: "+err.Error(),
		)

	} else {
		plan.Uuid = types.StringValue(response["UUID"])
		tflog.Info(ctx, "Experiment exists with name: "+plan.Name.String())
	}

	// Set state to fully populated data
	diags = resp.State.Set(ctx, plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
}

// Read refreshes the Terraform state with the latest data.
func (r *cloudlabvmResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	var state cloudlabvmModel
	diags := req.State.Get(ctx, &state)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
	response, status, err := r.client.experimentStatus(state.Name.String())
	if err != nil {
		resp.Diagnostics.AddError(
			"Error reading vm status",
			"Could not read vm status, unexpected error: "+err.Error(),
		)
		return
	}
	if status == EXPERIMENT_NOT_EXISTS {
		resp.State.RemoveResource(ctx)
		tflog.Info(ctx, "Experiment not exists")
	} else {
		state.Uuid = types.StringValue(response["UUID"])
		tflog.Info(ctx, "Experiment exists with name: "+state.Name.String())
		//Set state
		diags = resp.State.Set(ctx, &state)
	}

	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
}

// Update updates the resource and sets the updated Terraform state on success.
func (r *cloudlabvmResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	var plan cloudlabvmModel
	diags := req.Plan.Get(ctx, &plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
	resp.Diagnostics.AddError(
		"Error Updating VM",
		"Could not update vm, error: NOT IMPLEMENTED",
	)
	if resp.Diagnostics.HasError() {
		return
	}
}

// Delete deletes the resource and removes the Terraform state on success.
func (r *cloudlabvmResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var state cloudlabvmModel
	diags := req.State.Get(ctx, &state)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Delete existing order
	_, err := r.client.terminateExperiment(state.Uuid.String())
	if err != nil {
		resp.Diagnostics.AddError(
			"Error Deleting VM",
			"Could not delete VM, unexpected error: "+err.Error(),
		)
		return
	}
}
