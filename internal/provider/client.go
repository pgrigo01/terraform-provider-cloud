package provider

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"log"
	"mime/multipart"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"
)

const HostURL = "http://localhost:8080/"

// const HostURL = "http://155.98.36.7:8080/"
// const HostURL = "http://terraform-cloudlab.duckdns.org:8080/"

const experimentPath = "experiment"

const (
	EXPERIMENT_FAILED     = 1
	EXPERIMENT_READY      = 2
	EXPERIMENT_NOT_EXISTS = 3
)

// Profile UUIDs
// const profile_uuid = "3cfadd2c-e69d-11ee-9f39-e4434b2381fc" // giannis profile //terraform-profile
const profile_uuid = "d810b358-0416-11f0-af1a-e4434b2381fc"  // regular profile
const profile_uuid2 = "f661a302-e5a7-11e7-b179-90e2ba22fee4" // OpenStack (elastic) profile original
// const profile_uuid2 = "afab050d-0c2c-11f0-af1a-e4434b2381fc"  //openstack-terraform

// Client now has a new field "serverType" that can be set from the Terraform provider configuration.
type Client struct {
	credentialsPath string
	project         string
	elastic         bool   // true => use OpenStack (elastic) profile
	serverType      string // "chrome", "firefox" or "simple"
	browser         string // "chrome" or "firefox" or "simple"

}

// ensureFlaskRunning checks whether something is listening on localhost:8080.
// If not, it attempts to start the Flask server by calling selectServer.py with an optional server type.
func (c *Client) ensureFlaskRunning() error {
	timeout := 1 * time.Second
	conn, err := net.DialTimeout("tcp", "localhost:8080", timeout)
	if err == nil {
		// Server is already running, close the connection and return.
		conn.Close()
		return nil
	}

	log.Println("Flask server not running. Attempting to start it...")

	// Prepare command arguments.
	// The Python script is modified to accept an optional --server argument.
	var serverScript string
    switch c.browser {
    case "firefox":
        serverScript = "firefoxServer.py"
    default:
        serverScript = "chromeServer.py" // Default to Chrome
    }
    
    args := []string{serverScript}
    if c.serverType != "" {
        args = append(args, "--server", c.serverType)
    }
    cmd := exec.Command("python3", args...)

	// Redirect the Flask server's stdout and stderr so the user can view the server output (for credential prompts, etc).
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// Start the Flask server.
	if err := cmd.Start(); err != nil {
		log.Printf("Error starting Flask server: %v\n", err)
		return err
	}

	// Wait longer for the server to start - increased attempts and delay
	maxAttempts := 30             // Increased from 5 to 30 attempts
	retryDelay := 2 * time.Second // Increased from 1 to 2 seconds
	log.Printf("Waiting up to %d seconds for Flask server to start...", maxAttempts*int(retryDelay.Seconds()))

	for i := 0; i < maxAttempts; i++ {
		time.Sleep(retryDelay)
		conn, err := net.DialTimeout("tcp", "localhost:8080", timeout)
		if err == nil {
			conn.Close()
			log.Println("Flask server started successfully.")
			return nil
		}
		log.Printf("Waiting for Flask to start (attempt %d/%d)...", i+1, maxAttempts)
	}

	log.Println("WARNING: Flask server didn't respond within the timeout period.")
	log.Println("This could be due to credential decryption or initialization taking longer than expected.")

	return errors.New("failed to start Flask server after multiple attempts")
}

// mapToJSON converts the provided data into a JSON string.
func mapToJSON(data interface{}) (string, error) {
	jsonData, err := json.Marshal(data)
	if err != nil {
		return "", err
	}
	return string(jsonData), nil
}

// sendRequest sends an HTTP request to the Flask server at HostURL+apiPath with a multipart form payload.
// It ensures the Flask server is running by calling ensureFlaskRunning() before attempting the request.
func (c *Client) sendRequest(method string, apiPath string, params map[string]string) (string, int, error) {
	// Ensure that the Flask server is running before sending the request.
	if err := c.ensureFlaskRunning(); err != nil {
		return "Flask server is not available", -1, err
	}

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

	// Prepare bindings.
	bindings := make(map[string]interface{})
	if extraDiskSpace, ok := params["extra_disk_space"]; ok {
		delete(params, "extra_disk_space")
		bindings["extra_disk_space"] = extraDiskSpace
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

	// Write form fields.
	for key, value := range finalParams {
		if err := multipartWriter.WriteField(key, value); err != nil {
			return "Error writing form field", -1, err
		}
	}

	// Attach the file.
	file, err := os.Open(c.credentialsPath)
	if err != nil {
		return "Error opening file", -1, err
	}
	defer file.Close()

	fileField, err := multipartWriter.CreateFormFile("file", file.Name())
	if err != nil {
		return "Error creating form file field", -1, err
	}
	if _, err = io.Copy(fileField, file); err != nil {
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

// startExperiment sends a request to start an experiment.
func (c *Client) startExperiment(params map[string]string) (string, error) {
	response, _, err := c.sendRequest("POST", experimentPath, params)
	return response, err
}

// terminateExperiment sends a request to terminate an experiment (experiment ID is passed in the "experiment" field).
func (c *Client) terminateExperiment(identifier string) (string, error) {
	params := map[string]string{
		"experiment": identifier,
	}
	response, _, err := c.sendRequest("DELETE", experimentPath, params)
	return response, err
}

// experimentStatus sends a GET request to retrieve the status of an experiment by its name.
// The response is parsed into a map along with a corresponding status code.
func (c *Client) experimentStatus(experimentName string) (map[string]string, int, error) {
	params := map[string]string{
		"proj": func() string {
			return c.project
		}(),
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
		}
		return result, EXPERIMENT_READY, nil
	}
	if statusCode == 404 {
		return result, EXPERIMENT_NOT_EXISTS, nil
	}
	if err != nil {
		return result, -1, err
	}
	return result, -1, nil
}
