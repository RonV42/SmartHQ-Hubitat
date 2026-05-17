metadata {
    definition(
        name: "GE Profile Upper Oven",
        namespace: "RonV42",
        author: "Ron Vargo",
        description: "GE Profile Upper Oven via SmartHQ Bridge"
    ) {
        capability "Sensor"
        capability "Refresh"
        capability "TemperatureMeasurement"

        attribute "ovenState", "string"
        attribute "cookMode", "string"
        attribute "setTemperature", "number"
        attribute "actualTemperature", "number"
        attribute "cookTimeRemaining", "string"
        attribute "delayTimeRemaining", "string"
        attribute "kitchenTimer", "string"
        attribute "probePresent", "string"
        attribute "probeTemperature", "number"
        attribute "lightLevel", "string"
        attribute "remoteEnabled", "string"
        attribute "availableCookModes", "string"
        attribute "extendedCookModes", "string"
        
        command "setAttribute", [[name:"attribute*", type:"STRING"],
                         [name:"value*", type:"STRING"]]
    }


    preferences {
        input name: "logEnable", type: "bool", title: "Enable debug logging", defaultValue: true
    }
}

def setAttribute(String attribute, String value) {
    if (logEnable) log.debug "setAttribute: ${attribute} = ${value}"
    sendEvent(name: attribute, value: value)
}

def installed() {
    log.info "GE Profile Upper Oven installed"
    initialize()
}

def updated() {
    log.info "GE Profile Upper Oven updated"
    initialize()
}

def initialize() {
    if (logEnable) runIn(1800, logsOff)
}

def refresh() {
    log.info "Refresh requested - bridge maintains live connection"
}

def parse(String description) {
    log.debug "parse() called with: ${description}"
}

def updateAttributes(Map data) {
    if (logEnable) log.debug "updateAttributes: ${data}"
    data.each { key, value ->
        sendEvent(name: key, value: value)
    }
}

def logsOff() {
    log.warn "Debug logging disabled"
    device.updateSetting("logEnable", [value: "false", type: "bool"])
}
