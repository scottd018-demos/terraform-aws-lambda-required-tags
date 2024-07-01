variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type        = string
  default     = "required-tags-ec2"
  description = "Used for naming resources managed by this Terraform module.  Each resource created is prefixed with this value."
}

variable "required_tags" {
  type = object({
    keys   = list(string)
    values = list(string)
  })
  default = {
    keys   = ["required-tags-lambda"]
    values = ["true"]
  }
  description = <<EOF
  The required keys and values that are managed by this module.  Keys and Values must be the same length and each index 
  aligns with the index of the other list.  For example, key at position 0 has value at position 0.
  EOF

  validation {
    condition     = length(var.required_tags.keys) == length(var.required_tags.values)
    error_message = "'var.required_tags.keys' and 'var.required_tags.values' must have the same number of elements."
  }
}
