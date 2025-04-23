package provider

import (
        "context"
        "fmt"
        "strings"

        "github.com/hashicorp/terraform-plugin-framework/resource"
        "github.com/hashicorp/terraform-plugin-framework/resource/schema"
        "github.com/hashicorp/terraform-plugin-framework/types"
        "github.com/hashicorp/terraform-plugin-log/tflog"
)

// This resource uses the "elastic" (OpenStack) profile, so the
// provider's client.elastic = true for create/delete.

var (
        _ resource.Resource = &elasticVMResource{}
)

func ElasticVMResource() resource.Resource {
        return &elasticVMResource{}
}

type elasticVMResource struct {
        client Client
}

type elasticVMModel struct {
        Uuid             types.String `tfsdk:"uuid"`
        Name             types.String `tfsdk:"name"`
        Release          types.String `tfsdk:"release"`
        ComputeNodeCount types.Int64  `tfsdk:"compute_node_count"`
        OSNodeType       types.String `tfsdk:"os_node_type"`
        OSLinkSpeed      types.Int64  `tfsdk:"os_link_speed"`
        ML2Plugin        types.String `tfsdk:"ml2plugin"`
        ExtraImageURLs   types.String `tfsdk:"extra_image_urls"`
}

func (r *elasticVMResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
        // So that Terraform sees it as "cloudlab_elastic_vm"
        resp.TypeName = "cloudlab_openstack_experiment"
}

func (r *elasticVMResource) Schema(ctx context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
        resp.Schema = schema.Schema{
                Attributes: map[string]schema.Attribute{
                        "uuid": schema.StringAttribute{
                                Computed:    true,
                                Description: "Unique identifier for the elastic VM experiment.",
                        },
                        "name": schema.StringAttribute{
                                Required:    true,
                                Description: "The name of the elastic VM experiment.",
                        },
                        "release": schema.StringAttribute{
                                Required:    true,
                                Description: "The OpenStack release version to deploy (e.g., zed, xena, wallaby).",
                        },
                        "compute_node_count": schema.Int64Attribute{
                                Required:    true,
                                Description: "Number of compute nodes for the experiment.",
                        },
                        "os_node_type": schema.StringAttribute{
                                Required:    true,
                                Description: "The hardware type for the nodes.",
                        },
                        "os_link_speed": schema.Int64Attribute{
                                Optional:    true,
                                Description: "Network link speed in bits/s for the nodes. Defaults to 0 (any).",
                        },
                        "ml2plugin": schema.StringAttribute{
                                Required:    true,
                                Description: "The ML2 plugin to use (e.g., openvswitch, linuxbridge).",
                        },
                        "extra_image_urls": schema.StringAttribute{
                                Optional:    true,
                                Description: "Space-separated list of extra VM image URLs to download.",
                        },
                },
        }
}

func (r *elasticVMResource) Configure(ctx context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
        if req.ProviderData == nil {
                return
        }
        client, ok := req.ProviderData.(Client)
        if !ok {
                resp.Diagnostics.AddError(
                        "Unexpected Resource Configure Type",
                        fmt.Sprintf("Expected provider.Client, got: %T.", req.ProviderData),
                )
                return
        }
        // Mark the client as elastic so we pass only the "name" to terminate
        client.elastic = true
        r.client = client
}

func (r *elasticVMResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
        var plan elasticVMModel
        diags := req.Plan.Get(ctx, &plan)
        resp.Diagnostics.Append(diags...)
        if resp.Diagnostics.HasError() {
                return
        }

        // Build param map for the server:
        params := map[string]string{
                "name":             plan.Name.ValueString(),
                "release":          plan.Release.ValueString(),
                "computeNodeCount": fmt.Sprintf("%d", plan.ComputeNodeCount.ValueInt64()),
                "osNodeType":       plan.OSNodeType.ValueString(),
                "osLinkSpeed":      fmt.Sprintf("%d", plan.OSLinkSpeed.ValueInt64()),
                "ml2plugin":        plan.ML2Plugin.ValueString(),
                "extraImageURLs":   plan.ExtraImageURLs.ValueString(),
        }

        // Start the experiment (the "elastic" profile).
        response, err := r.client.startExperiment(params)
        if err != nil {
                resp.Diagnostics.AddError(
                        "Error Creating Elastic VM",
                        "Could not create elastic VM: "+err.Error(),
                )
                return
        }

        // Attempt to parse out the UUID from the server's response:
        plan.Uuid = types.StringValue(parseUUID(response))

        // Save state
        diags = resp.State.Set(ctx, plan)
        resp.Diagnostics.Append(diags...)
}

// parseUUID attempts to find a line like "UUID: abcd..." in the response.
func parseUUID(response string) string {
        lines := strings.Split(response, "\n")
        for _, line := range lines {
                if strings.Contains(line, "UUID") {
                        parts := strings.Split(line, ":")
                        if len(parts) == 2 {
                                return strings.TrimSpace(parts[1])
                        }
                }
        }
        return ""
}

func (r *elasticVMResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
        var state elasticVMModel
        diags := req.State.Get(ctx, &state)
        resp.Diagnostics.Append(diags...)
        if resp.Diagnostics.HasError() {
                return
        }

        // Check if it still exists
        _, status, err := r.client.experimentStatus(state.Name.ValueString())
        if err != nil {
                resp.Diagnostics.AddError(
                        "Error Reading Elastic VM Status",
                        "Could not read status: "+err.Error(),
                )
                return
        }
        if status == EXPERIMENT_NOT_EXISTS {
                resp.State.RemoveResource(ctx)
                return
        }

        // If it still exists, keep the same data. The server might not return
        // a distinct "UUID" for an elastic experiment, but if it does,
        // we could do something like parse it again here.
        diags = resp.State.Set(ctx, &state)
        resp.Diagnostics.Append(diags...)
}

func (r *elasticVMResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
        resp.Diagnostics.AddError("Update Not Implemented", "This resource does not support updates.")
}

func (r *elasticVMResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
        var state elasticVMModel
        diags := req.State.Get(ctx, &state)
        resp.Diagnostics.Append(diags...)
        if resp.Diagnostics.HasError() {
                return
        }

        //_, err := r.client.terminateExperiment(state.Uuid.ValueString())
        _, err := r.client.terminateExperiment(state.Name.ValueString())
        if err != nil {
                resp.Diagnostics.AddError(
                        "Error Deleting VM",
                        "Could not delete VM, unexpected error: "+err.Error(),
                )
                return
        }
        tflog.Info(ctx, "[Delete] Experiment terminated.")
}