package provider

import (
	"context"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/types"
)

// Ensure the implementation satisfies the expected interfaces.
var (
	_ resource.Resource = &cloudlabExperimentResource{}
)

// CloudLabExperimentResource is a helper function to simplify the provider implementation.
func CloudLabExperimentResource() resource.Resource {
	return &cloudlabExperimentResource{}
}

// cloudlabExperimentResource is the resource implementation.
type cloudlabExperimentResource struct{}

// Metadata returns the resource type name.
func (r *cloudlabExperimentResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_cloudlab"
}

// orderResourceModel maps the resource schema data.
type cloudlabExperimentModel struct {
	project      types.String `tfsdk:"project"`
	profile_uuid types.String `tfsdk:"profile_uuid"`
	name         types.String `tfsdk:"name"`
}

// Schema defines the schema for the resource.
func (r *cloudlabExperimentResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
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
		},
	}
}

// Create creates the resource and sets the initial Terraform state.
func (r *cloudlabExperimentResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	// Retrieve values from plan
	var plan cloudlabExperimentModel
	diags := req.Plan.Get(ctx, &plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Create new experiment
	// Run script
	order, err := r.client.CreateOrder(items)
	if err != nil {
		resp.Diagnostics.AddError(
			"Error creating order",
			"Could not create order, unexpected error: "+err.Error(),
		)
		return
	}

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

	// Set state to fully populated data
	diags = resp.State.Set(ctx, plan)
	resp.Diagnostics.Append(diags...)
	if resp.Diagnostics.HasError() {
		return
	}
}

// Read refreshes the Terraform state with the latest data.
func (r *cloudlabExperimentResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
}

// Update updates the resource and sets the updated Terraform state on success.
func (r *cloudlabExperimentResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
}

// Delete deletes the resource and removes the Terraform state on success.
func (r *cloudlabExperimentResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
}
