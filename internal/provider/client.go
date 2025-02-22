package provider

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"strings"
)

// const HostURL = "http://localhost:8080/"

const HostURL = "155.98.36.7/8080" 


const experimentPath = "experiment"

const profile_uuid = "3cfadd2c-e69d-11ee-9f39-e4434b2381fc"

const (
	EXPERIMENT_FAILED     = 1
	EXPERIMENT_READY      = 2
	EXPERIMENT_NOT_EXISTS = 3
)

type Client struct {
	credentialsPath string
	project         string
}

func (c *Client) startExperiment(params map[string]string) (string, error) {
	response, _, err := c.sendRequest("POST", experimentPath, params)
	return response, err
}

func (c *Client) terminateExperiment(experimentUuid string) (string, error) {
	params := map[string]string{
		"proj":       c.project,
		"profile":    profile_uuid,
		"experiment": experimentUuid,
	}
	response, _, err := c.sendRequest("DELETE", experimentPath, params)
	return response, err
}

func (c *Client) experimentStatus(experimentName string) (map[string]string, int, error) {
	params := map[string]string{
		"proj":       c.project,
		"profile":    profile_uuid,
		"experiment": experimentName,
	}
	response, statusCode, err := c.sendRequest("GET", experimentPath, params)
	result := make(map[string]string)
	// Result type: map[string]string{
	//					Status: ready
	//					UUID: uuid-uuid-uuid...
	//					wbstore: ...
	//					Execute Services (running/finished/failed): 0/1/0
	//				}

	lines := strings.Split(response, "\n")
	for _, line := range lines {
		parts := strings.Split(line, ":")
		if len(parts) == 2 {
			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			result[key] = value
		}
	}

	if statusCode == 200 {
		if result["Status"] == "failed" {
			return result, EXPERIMENT_FAILED, nil
		} else {
			return result, EXPERIMENT_READY, nil
		}
	}
	if statusCode == 404 {
		return result, EXPERIMENT_NOT_EXISTS, nil
	}
	if err != nil {
		return result, -1, err
	}
	return result, -1, nil
}

func mapToJSON(data interface{}) (string, error) {
	// Convert the data to JSON
	jsonData, err := json.Marshal(data)
	if err != nil {
		return "", err
	}

	// Convert the JSON data to a string
	jsonString := string(jsonData)

	return jsonString, nil
}

func (c *Client) sendRequest(method string, apiPath string, params map[string]string) (string, int, error) {
	finalParams := map[string]string{
		"proj":       c.project,
		"profile":    profile_uuid,
		"name":       params["name"],
		"experiment": params["experiment"],
	}
	delete(params, "name")
	bindingsJson, err := mapToJSON(params)
	if err != nil {
		return "Error converting to json: ", -1, err
	}
	finalParams["bindings"] = bindingsJson
	// Create a buffer to store the request body
	requestBuffer := new(bytes.Buffer)

	// Create a new multipart writer
	multipartWriter := multipart.NewWriter(requestBuffer)

	// Add parameters to the request
	for key, value := range finalParams {
		_ = multipartWriter.WriteField(key, value)
	}

	// Open the file
	file, err := os.Open(c.credentialsPath)
	if err != nil {
		return "Error opening file", -1, err
	}
	defer file.Close()

	// Create a form file field
	fileField, err := multipartWriter.CreateFormFile("file", file.Name())
	if err != nil {
		return "Error creating form file field", -1, err
	}

	// Copy the file contents to the form file field
	_, err = io.Copy(fileField, file)
	if err != nil {
		return "Error copying file contents", -1, err
	}

	// Close the multipart writer to finalize the request body
	multipartWriter.Close()

	// Create a new request with method and URL with parameters
	request, err := http.NewRequest(method, HostURL+apiPath, requestBuffer)
	if err != nil {
		return "Error creating request", -1, err
	}

	// Set the content type for the file upload
	request.Header.Set("Content-Type", multipartWriter.FormDataContentType())

	// Perform the request
	client := http.Client{}
	response, err := client.Do(request)
	if err != nil {
		return "Error sending request", -1, err
	}
	// Print body
	body, err := io.ReadAll(response.Body)
	if err != nil {
		return "Error reading response body", -1, err
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		return string(body), response.StatusCode, errors.New(string(body))
	}
	return string(body), response.StatusCode, nil
}
