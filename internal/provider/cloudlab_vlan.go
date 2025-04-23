package provider

import (
    "context"
    "fmt"
    "github.com/hashicorp/terraform-plugin-framework/resource"
    "github.com/hashicorp/terraform-plugin-framework/resource/schema"
    "github.com/hashicorp/terraform-plugin-framework/types"
)

var (
    _ resource.Resource = &cloudlabVlanResource{}
)

func CloudLabVlanResource() resource.Resource {
    return &cloudlabVlanResource{}
}

type cloudlabVlanResource struct {
    client Client
}

func (r *cloudlabVlanResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
    resp.TypeName = "cloudlab_vlan"
}

type cloudlabVlanModel struct {
    Name        types.String `tfsdk:"name"`
    Subnet_mask types.String `tfsdk:"subnet_mask"`
}

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

func (r *cloudlabVlanResource) Configure(ctx context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
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

func (r *cloudlabVlanResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
    var plan cloudlabVlanModel
    diags := req.Plan.Get(ctx, &plan)
    resp.Diagnostics.Append(diags...)
    if resp.Diagnostics.HasError() {
        return
    }
    diags = resp.State.Set(ctx, plan)
    resp.Diagnostics.Append(diags...)
}

func (r *cloudlabVlanResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
    var state cloudlabVlanModel
    diags := req.State.Get(ctx, &state)
    resp.Diagnostics.Append(diags...)
    if resp.Diagnostics.HasError() {
        return
    }
    diags = resp.State.Set(ctx, &state)
    resp.Diagnostics.Append(diags...)
}

func (r *cloudlabVlanResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
}

func (r *cloudlabVlanResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
}
