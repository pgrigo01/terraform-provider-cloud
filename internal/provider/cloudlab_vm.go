package provider

import (
	"context"
	"fmt"
	"strings"

	"github.com/hashicorp/terraform-plugin-framework-validators/stringvalidator"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/schema/validator"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
)

var (
	_ resource.Resource = &cloudlabvmResource{}
)

func CloudLabExperimentResource() resource.Resource {
	return &cloudlabvmResource{}
}

type cloudlabvmResource struct {
	client Client
}

func (r *cloudlabvmResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = "cloudlab_simple_experiment"
}

type cloudlabvmModel struct {
	Uuid             types.String        `tfsdk:"uuid"`
	Name             types.String        `tfsdk:"name"`
	Aggregate        types.String        `tfsdk:"aggregate"`
	Image            types.String        `tfsdk:"image"`
	Routable_ip      types.Bool          `tfsdk:"routable_ip"`
	Extra_disk_space types.Int64         `tfsdk:"extra_disk_space"`
	Node_count       types.Int64         `tfsdk:"node_count"`
	Vlans            []cloudlabVlanModel `tfsdk:"vlans"`
}

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
			"extra_disk_space": schema.Int64Attribute{
				Optional:    true,
				Description: "Size of extra_disk_space storage in GB to mount at /mydata. 0 means no extra_disk_space is mounted.",
			},
			"node_count": schema.Int64Attribute{
				Optional:    true,
				Description: "Number of nodes to create (1-10)",
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
	if req.ProviderData == nil {
		return
	}
	client, ok := req.ProviderData.(Client)
	if !ok {
		resp.Diagnostics.AddError(
			"Unexpected Resource Configure Type",
			fmt.Sprintf("Expected *provider.Client, got: %T.", req.ProviderData),
		)
		return
	}
	r.client = client
}

func (r *cloudlabvmResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	// Retrieve values from plan.
	var plan cloudlabvmModel
	diags := req.Plan.Get(ctx, &plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Log the raw strings for debugging
	tflog.Info(ctx, "[Create] plan.Image="+plan.Image.ValueString())
	tflog.Info(ctx, "[Create] plan.Aggregate="+plan.Aggregate.ValueString())
	tflog.Info(ctx, "[Create] plan.Routable_ip="+fmt.Sprintf("%v", plan.Routable_ip.ValueBool()))

	// Compute the full experiment name from plan.Name + workspace
	baseName := plan.Name.ValueString()
	// workspace := r.client.workspace
	// if workspace == "" {
	//     workspace = "default"
	// }
	// computedName := fmt.Sprintf("%s-%s", baseName, workspace)

	// Build a JSON list for any VLANs
	sharedvlans := func() string {
		var vlans []map[string]string
		for _, vlan := range plan.Vlans {
			vlans = append(vlans, map[string]string{
				"name":        strings.ReplaceAll(vlan.Name.ValueString(), "\"", ""),
				"subnet_mask": strings.ReplaceAll(vlan.Subnet_mask.ValueString(), "\"", ""),
			})
		}
		vlansJson, err := mapToJSON(vlans)
		if err != nil {
			resp.Diagnostics.AddError(
				"Error converting VLANs to json",
				"Error: "+err.Error(),
			)
			return ""
		}
		return vlansJson
	}()

	// Prepare parameters to send to the client
	params := map[string]string{
		"name":        baseName,
		"routable_ip": plan.Routable_ip.String(),
	}

	// Add extra_disk_space storage if specified
	if !plan.Extra_disk_space.IsNull() {
		params["extra_disk_space"] = fmt.Sprintf("%d", plan.Extra_disk_space.ValueInt64())
		tflog.Info(ctx, fmt.Sprintf("[Create] Adding extra_disk_space storage: %d GB", plan.Extra_disk_space.ValueInt64()))
	}

	// Handle node count
	nodeCount := int64(1) // default to 1
	if !plan.Node_count.IsNull() {
		nodeCount = plan.Node_count.ValueInt64()
	}
	params["node_count"] = fmt.Sprintf("%d", nodeCount)
	tflog.Info(ctx, fmt.Sprintf("[Create] Setting node count to: %d", nodeCount))

	// Convert friendly "UBUNTU 20.04" -> "urn:publicid:IDN+emulab.net+image+..."
	AddImageParam(ctx, &params, plan.Image.ValueString())
	// Convert friendly "Any" -> ""
	AddAggregateParam(ctx, &params, plan.Aggregate.ValueString())

	if len(plan.Vlans) != 0 {
		params["sharedVlans"] = sharedvlans
	}

	// ADDED for debug: show final param map
	tflog.Info(ctx, fmt.Sprintf("[Create] Final param map = %#v", params))

	_, err := r.client.startExperiment(params)
	if err != nil {
		resp.Diagnostics.AddError(
			"Error creating vm",
			"Could not create vm, unexpected error: "+err.Error(),
		)
		return
	}

	// Query status for the experiment
	response, status, err := r.client.experimentStatus(baseName)
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
			"vm status not exists, unexpected error: experiment not found",
		)
		return
	} else {
		plan.Uuid = types.StringValue(response["UUID"])
		tflog.Info(ctx, "[Create] Experiment exists with name: "+baseName)
	}

	// Save state
	diags = resp.State.Set(ctx, plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
}

func (r *cloudlabvmResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	var state cloudlabvmModel
	diags := req.State.Get(ctx, &state)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	baseName := state.Name.ValueString()
	// workspace := r.client.workspace
	// if workspace == "" {
	//     workspace = "default"
	// }
	// computedName := fmt.Sprintf("%s-%s", baseName, workspace)

	response, status, err := r.client.experimentStatus(baseName)
	if err != nil {
		resp.Diagnostics.AddError(
			"Error reading vm status",
			"Could not read vm status, unexpected error: "+err.Error(),
		)
		return
	}
	if status == EXPERIMENT_NOT_EXISTS {
		// If it no longer exists, remove from state
		resp.State.RemoveResource(ctx)
		tflog.Info(ctx, "[Read] Experiment not exists, removing from state.")
		return
	}

	// Keep the same plan data
	state.Uuid = types.StringValue(response["UUID"])
	diags = resp.State.Set(ctx, &state)
	resp.Diagnostics.Append(diags...)
}

func (r *cloudlabvmResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	// Not implemented
	resp.Diagnostics.AddError("Update not implemented", "This resource does not support updates yet.")
}

func (r *cloudlabvmResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var state cloudlabvmModel
	diags := req.State.Get(ctx, &state)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	_, err := r.client.terminateExperiment(state.Uuid.ValueString())
	if err != nil {
		resp.Diagnostics.AddError(
			"Error Deleting VM",
			"Could not delete VM, unexpected error: "+err.Error(),
		)
		return
	}
	tflog.Info(ctx, "[Delete] Experiment terminated.")
}
