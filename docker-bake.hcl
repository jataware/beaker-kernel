variable "DOCKER_REGISTRY" {
  default = "ghcr.io"
}
variable "DOCKER_ORG" {
  default = "darpa-askem"
}
variable "VERSION" {
  default = "local"
}

# ----------------------------------------------------------------------------------------------------------------------

function "tag" {
  params = [image_name, prefix, suffix]
  result = [ "${DOCKER_REGISTRY}/${DOCKER_ORG}/${image_name}:${check_prefix(prefix)}${VERSION}${check_suffix(suffix)}" ]
}

function "check_prefix" {
  params = [tag]
  result = notequal("",tag) ? "${tag}-": ""
}

function "check_suffix" {
  params = [tag]
  result = notequal("",tag) ? "-${tag}": ""
}

# ----------------------------------------------------------------------------------------------------------------------

group "prod" {
  targets = ["jupyter-llm", "beaker-kernel"]
}

group "default" {
  targets = ["jupyter-llm-base", "beaker-kernel-base"]
}

# ----------------------------------------------------------------------------------------------------------------------

target "_platforms" {
  platforms = ["linux/amd64"]
}

target "jupyter-llm-base" {
	context = "."
	tags = tag("jupyter-llm", "", "")
	dockerfile = "Dockerfile"
}

target "beaker-kernel-base" {
	context = "."
	tags = tag("beaker-kernel", "", "")
	dockerfile = "Dockerfile"
}

target "jupyter-llm" {
  inherits = ["_platforms", "jupyter-llm-base"]
}

target "beaker-kernel" {
  inherits = ["_platforms", "beaker-kernel-base"]
}
