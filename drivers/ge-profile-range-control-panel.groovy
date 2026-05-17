metadata {
    definition(
        name: "GE Profile Range Control Panel",
        namespace: "RonV42",
        author: "Ron Vargo",
        description: "GE Profile Range Control Panel via SmartHQ Bridge"
    ) {
        capability "Sensor"
        capability "Refresh"

        attribute "interfaceLocked", "string"
        attribute "sabbathMode", "string"
        attribute "soundLevel", "string"
        attribute "endTone", "string"
        attribute "convectionConversion", "string"
        attribute "twelveHourShutoff", "string"
        attribute "clockFormat", "string"
        attribute "wifiVersion", "string"
        attribute "online", "string"
        attribute "brand", "string"
        attribute "modelNumber", "string"
        attribute "serialNumber", "string"
        
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
    log.info "GE Profile Range Control Panel installed"
    initialize()
}

def updated() {
    log.info "GE Profile Range Control Panel updated"
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

// Called by bridge via Maker API
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
