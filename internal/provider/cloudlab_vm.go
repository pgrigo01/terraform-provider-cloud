package provider

import (
	"context"
	"fmt"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
	"github.com/hashicorp/terraform-plugin-log/tflog"
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

// orderResourceModel maps the resource schema data.
type cloudlabvmModel struct {
	ID           types.String `tfsdk:"id"`
	Project      types.String `tfsdk:"project"`
	Profile_uuid types.String `tfsdk:"profile_uuid"`
	Name         types.String `tfsdk:"name"`
	Vlan         types.Int64  `tfsdk:"vlan"`
}

// Schema defines the schema for the resource.
func (r *cloudlabvmResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"id": schema.StringAttribute{
				Computed: true,
			},
			"project": schema.StringAttribute{
				Required:  true,
				Sensitive: true,
			},
			"profile_uuid": schema.StringAttribute{
				Required: true,
			},
			"name": schema.StringAttribute{
				Required: true,
			},
			"vlan": &schema.ListAttribute{
				ElementType: types.Int64Type,
				Required:    true,
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

	// Create new vm
	// Run script

	//order, err := r.client.CreateOrder(items)
	//if err != nil {
	//	resp.Diagnostics.AddError(
	//		"Error creating order",
	//		"Could not create order, unexpected error: "+err.Error(),
	//	)
	//	return
	//}

	//// Map response body to schema and populate Computed attribute values
	//plan.ID = types.StringValue(strconv.Itoa(order.ID))
	//for orderItemIndex, orderItem := range order.Items {
	//	plan.Items[orderItemIndex] = orderItemModel{
	//		Coffee: orderItemCoffeeModel{
	//			ID:          types.Int64Value(int64(orderItem.Coffee.ID)),
	//			Name:        types.StringValue(orderItem.Coffee.Name),
	//			Teaser:      types.StringValue(orderItem.Coffee.Teaser),
	//			Description: types.StringValue(orderItem.Coffee.Description),
	//			Price:       types.Float64Value(orderItem.Coffee.Price),
	//			Image:       types.StringValue(orderItem.Coffee.Image),
	//		},
	//		Quantity: types.Int64Value(int64(orderItem.Quantity)),
	//	}
	//}
	//plan.LastUpdated = types.StringValue(time.Now().Format(time.RFC850))

	_, err := r.client.startExperiment(map[string]string{
		"key": "Value",
	})

	if err != nil {
		resp.Diagnostics.AddError(
			"Error creating order",
			"Could not create vm, unexpected error: "+err.Error(),
		)
		return
	}
	tflog.Info(ctx, fmt.Sprintf("Hello World Vlan: %d", plan.Vlan))

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
	state.ID = types.StringValue("placeholder")
	// Set state
	diags := resp.State.Set(ctx, &state)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
}

// Update updates the resource and sets the updated Terraform state on success.
func (r *cloudlabvmResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
}

// Delete deletes the resource and removes the Terraform state on success.
func (r *cloudlabvmResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
}
