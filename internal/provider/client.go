package provider

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"log" // ADDED for debug
	"mime/multipart"
	"net/http"
	"os"
	"strings"
)

const HostURL = "http://localhost:8080/"

//const HostURL = "http://155.98.36.7:8080/"
//const HostURL = "http://terraform-cloudlab.duckdns.org:8080/"

const experimentPath = "experiment"

// const profile_uuid = "3cfadd2c-e69d-11ee-9f39-e4434b2381fc" //giannis profile //terraform-profile
const profile_uuid = "d810b358-0416-11f0-af1a-e4434b2381fc"  // regular profile
const profile_uuid2 = "f661a302-e5a7-11e7-b179-90e2ba22fee4" // OpenStack (elastic) profile original
// const profile_uuid2 = "afab050d-0c2c-11f0-af1a-e4434b2381fc"  //openstack-terraform
const (
	EXPERIMENT_FAILED     = 1
	EXPERIMENT_READY      = 2
	EXPERIMENT_NOT_EXISTS = 3
)

type Client struct {
	credentialsPath string
	project         string
	// workspace       string
	elastic         bool // true => use OpenStack (elastic) profile
}

func (c *Client) startExperiment(params map[string]string) (string, error) {
	response, _, err := c.sendRequest("POST", experimentPath, params)
	return response, err
}

// terminateExperiment always sends the experiment's UUID in the "experiment" field.
func (c *Client) terminateExperiment(identifier string) (string, error) {
	params := map[string]string{
		"experiment": identifier,
	}
	response, _, err := c.sendRequest("DELETE", experimentPath, params)
	return response, err
}

func (c *Client) experimentStatus(experimentName string) (map[string]string, int, error) {
	params := map[string]string{
		"proj": c.project,
		"profile": func() string {
			if c.elastic {
				return profile_uuid2
			}
			return profile_uuid
		}(),
		"experiment": experimentName,
	}
	response, statusCode, err := c.sendRequest("GET", experimentPath, params)
	result := make(map[string]string)

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
	jsonData, err := json.Marshal(data)
	if err != nil {
		return "", err
	}
	return string(jsonData), nil
}

func (c *Client) sendRequest(method string, apiPath string, params map[string]string) (string, int, error) {
	finalParams := map[string]string{
		"proj": c.project,
		"profile": func() string {
			if c.elastic {
				return profile_uuid2
			}
			return profile_uuid
		}(),
		"name":       params["name"],
		"experiment": params["experiment"],
	}
	delete(params, "name")
	delete(params, "experiment")
	bindings := make(map[string]interface{})
	if extra_disk_space, ok := params["extra_disk_space"]; ok {
		delete(params, "extra_disk_space")
		bindings["extra_disk_space"] = extra_disk_space
	}
	if nodeCount, ok := params["node_count"]; ok {
		bindings["node_count"] = nodeCount
	} else {
		bindings["node_count"] = "1" // default
	}
	for k, v := range params {
		bindings[k] = v
	}

	bindingsJson, err := mapToJSON(bindings)
	if err != nil {
		return "Error converting to json", -1, err
	}
	finalParams["bindings"] = bindingsJson

	log.Printf("[sendRequest] finalParams before sending = %#v\n", finalParams)
	log.Printf("[sendRequest] bindingsJson = %s\n", bindingsJson)

	requestBuffer := new(bytes.Buffer)
	multipartWriter := multipart.NewWriter(requestBuffer)

	for key, value := range finalParams {
		_ = multipartWriter.WriteField(key, value)
	}

	file, err := os.Open(c.credentialsPath)
	if err != nil {
		return "Error opening file", -1, err
	}
	defer file.Close()

	fileField, err := multipartWriter.CreateFormFile("file", file.Name())
	if err != nil {
		return "Error creating form file field", -1, err
	}
	_, err = io.Copy(fileField, file)
	if err != nil {
		return "Error copying file contents", -1, err
	}

	multipartWriter.Close()

	req, err := http.NewRequest(method, HostURL+apiPath, requestBuffer)
	if err != nil {
		return "Error creating request", -1, err
	}
	req.Header.Set("Content-Type", multipartWriter.FormDataContentType())

	client := http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "Error sending request", -1, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "Error reading response body", -1, err
	}

	if resp.StatusCode != 200 {
		return string(body), resp.StatusCode, errors.New(string(body))
	}
	return string(body), resp.StatusCode, nil
}
