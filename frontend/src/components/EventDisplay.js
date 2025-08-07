import React from 'react';

class EventDisplay extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            audioInputIndex: 0,
            eventsByContentName: [],
            selectedEvent: null,
            showEventJson: false,
        };
    }

    cleanup() {
        this.setState({
            eventsByContentName: [], 
            audioInputIndex: 0,
            selectedEvent: null,
            showEventJson: false
        });
    }
    
    displayEvent(event, type) {
        if (event && event.event) {
            const eventName = Object.keys(event?.event)[0];
            let key = null;
            let ts = Date.now();
            let interrupted = false;
            const contentType = event.event[eventName].type;
            const contentName = event.event[eventName].contentName;
            const contentId = event.event[eventName].contentId;

            if (eventName === "audioOutput") {
                key = `${eventName}-${contentId}`;
                // truncate event audio content
                if (event.event.audioOutput.content) {
                    event.event.audioOutput.content = event.event.audioOutput.content.substr(0,10) + "...";
                }
            }
            else if (eventName === "audioInput") {
                key = `${eventName}-${contentName}-${this.state.audioInputIndex}`;
            }
            else if (eventName === "contentStart" || eventName === "textInput" || eventName === "contentEnd") {
                key = `${eventName}-${contentName}-${contentType}`;
                if (type === "in" && event.event[eventName].type === "AUDIO") {
                    this.setState({audioInputIndex: this.state.audioInputIndex + 1});
                }
                else if(type === "out") {
                    key = `${eventName}-${contentName}-${contentType}-${ts}`;
                }
            }
            else if(eventName === "textOutput") {
                const role = event.event[eventName].role;
                const content = event.event[eventName].content;
                if (role === "ASSISTANT" && content && content.startsWith("{")) {
                    try {
                        const evt = JSON.parse(content);
                        interrupted = evt.interrupted === true;
                    } catch (e) {
                        // Not JSON, continue normally
                    }
                }
                key = `${eventName}-${ts}`;
            }
            else if (eventName === "toolUse") {
                key = `${eventName}-${ts}`;
            }
            else {
                key = `${eventName}-${ts}`;
            }

            let eventsByContentName = this.state.eventsByContentName;
            if (eventsByContentName === null)
                eventsByContentName = [];

            let exists = false;
            for(var i=0;i<eventsByContentName.length;i++) {
                var item = eventsByContentName[i];
                if (item.key === key && item.type === type) {
                    item.events.push(event);
                    item.interrupted = interrupted;
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                const item = {
                    key: key, 
                    name: eventName, 
                    type: type, 
                    events: [event], 
                    ts: ts,
                    interrupted: interrupted
                };
                eventsByContentName.unshift(item);
            }
            this.setState({eventsByContentName: eventsByContentName});
        }
    }

    handleEventClick = (event) => {
        this.setState({
            selectedEvent: event,
            showEventJson: !this.state.showEventJson
        });
    }

    getEventClassName(event) {
        let className = "";
        
        if (event.type === "in") {
            if (event.name === "toolUse") {
                className = "event-tool";
            } else {
                className = "event-in";
            }
        } else {
            className = "event-out";
        }
        
        if (event.interrupted) {
            className = "event-int";
        }
        
        return className;
    }

    render() {
        return (
            <div className="events-display">
                {this.state.eventsByContentName.map((event, index) => (
                    <div 
                        key={index}
                        className={this.getEventClassName(event)}
                        onClick={() => this.handleEventClick(event)}
                        title="Click to view details"
                    >
                        <div>
                            {event.type === "in" ? "← " : "→ "}{event.name}
                            {event.events.length > 1 ? ` (${event.events.length})` : ""}
                        </div>
                        
                        {this.state.selectedEvent === event && this.state.showEventJson && (
                            <div className="tooltip" style={{display: 'block'}}>
                                <pre>{JSON.stringify(event.events[event.events.length - 1], null, 2)}</pre>
                            </div>
                        )}
                    </div>
                ))}
                
                {this.state.eventsByContentName.length === 0 && (
                    <div style={{color: '#666', fontStyle: 'italic', padding: '20px', textAlign: 'center'}}>
                        No events yet. Start a conversation to see events here.
                    </div>
                )}
            </div>
        );
    }
}

export default EventDisplay;
