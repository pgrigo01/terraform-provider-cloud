package provider

import (
	"bytes"
	"errors"
	"io"
	"io/ioutil"
	"mime/multipart"
	"net/http"
	"os"
)

const HostURL = "http://localhost:8080/"

const StartExperimentPath = "startExperiment"

type Client struct {
	credentialsPath string
}

func (c *Client) startExperiment(params map[string]string) (string, error) {
	return c.sendRequest(StartExperimentPath, params)
}

func (c *Client) sendRequest(apiPath string, params map[string]string) (string, error) {
	// Create a buffer to store the request body
	requestBuffer := new(bytes.Buffer)

	// Create a new multipart writer
	multipartWriter := multipart.NewWriter(requestBuffer)

	// Add parameters to the request
	for key, value := range params {
		_ = multipartWriter.WriteField(key, value)
	}

	// Open the file
	file, err := os.Open(c.credentialsPath)
	if err != nil {
		return "Error opening file", err
	}
	defer file.Close()

	// Create a form file field
	fileField, err := multipartWriter.CreateFormFile("file", file.Name())
	if err != nil {
		return "Error creating form file field", err
	}

	// Copy the file contents to the form file field
	_, err = io.Copy(fileField, file)
	if err != nil {
		return "Error copying file contents", err
	}

	// Close the multipart writer to finalize the request body
	multipartWriter.Close()

	// Create a new request with "GET" method and URL with parameters
	request, err := http.NewRequest("GET", HostURL+apiPath, requestBuffer)
	if err != nil {
		return "Error creating request", err
	}

	// Set the content type for the file upload
	request.Header.Set("Content-Type", multipartWriter.FormDataContentType())

	// Perform the request
	client := http.Client{}
	response, err := client.Do(request)
	if err != nil {
		return "Error sending request", err
	}
	// Print body
	body, err := ioutil.ReadAll(response.Body)
	if err != nil {
		return "Error reading response body", err
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		return string(body), errors.New(string(body))
	}
	return "Success", nil
}
