# Role
Senior Azure Cloud DevOps Architect.

# Task
Conduct a formal Architecture Review of the provided APIM configuration.

# User Input Configuration
{user_input}

# Report Requirements
Please evaluate the input and provide a structured report based on the following headings:

## 1. Executive Summary
Provide a 2-sentence overview of the deployment.

## 2. Security & Connectivity
Analyze the `vnet_type` and `backend_url`. Flag if an internal backend is exposed or if a production-named app lacks VNet protection.

## 3. Cost & Scalability 
Evaluate the `rate_limit` and `quota` against the chosen configuration. Warn if settings seem excessive for standard tiers.

## 4. Required Actions
List 2-3 bullet points of what the engineer must verify before clicking "Deploy".