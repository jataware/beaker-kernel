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

function "buildtag" {
  params = [image_name, prefix, suffix]
  result = [ "${DOCKER_REGISTRY}/${DOCKER_ORG}/${image_name}:${check_prefix(prefix)}${VERSION}${check_suffix(suffix)}", "${image_name}:build" ]
}

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
  targets = ["beaker-kernel", "askem-julia-base"]
}

group "default" {
  targets = ["beaker-kernel-base"]
}

# ----------------------------------------------------------------------------------------------------------------------

target "_platforms" {
  platforms = ["linux/amd64"]
}

target "askem-julia-base" {
    inherits = ["_platforms"]
	context = "environments/julia/"
	tags = buildtag("askem-julia-base", "", "")
	dockerfile = "Dockerfile"
}

target "beaker-kernel-base" {
    contexts = {
        askem-julia-base = "target:askem-julia-base"
    }
	context = "."
	tags = tag("beaker-kernel", "", "")
	dockerfile = "Dockerfile"
    args = {
        JULIA_IMAGE = "askem-julia-base"
    }
}

target "beaker-kernel" {
  inherits = ["_platforms", "beaker-kernel-base"]
}
