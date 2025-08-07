import { useState, useRef } from "react";
import * as React from "react";
import { AppLayout, SideNavigation } from '@cloudscape-design/components';
import TopNavigation from "@cloudscape-design/components/top-navigation";
import VoiceAgent from './VoiceAgent';
import './App.css';

const ITEMS = [
  {
    type: "link",
    text: "Voice Chat",
    id: "voice-chat",
    href: "#/voice-chat",
  }
];

function App() {
  const [currentPage, setCurrentPage] = useState("voice-chat");
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [activeNavHref, setActiveNavHref] = useState("#/voice-chat");
  const [displayTopMenu] = useState(window.self === window.top);

  const appLayout = useRef();

  const handleNavigationChange = () => {
    setNavigationOpen(!navigationOpen);
  };

  const handleNavItemClick = e => {
    setCurrentPage(e.detail.id);
    setActiveNavHref("#/" + e.detail.id);
  };

  const handleTopClick = e => {
    setCurrentPage("voice-chat");
    setActiveNavHref("#/voice-chat");
    setNavigationOpen(false);
  };

  return (
    <div>
      {displayTopMenu && (
        <TopNavigation
          identity={{
            href: "#",
            title: "AWS Strands Nova Voice Assistant",
            onFollow: handleTopClick
          }}
          i18nStrings={{
            searchIconAriaLabel: "Search",
            searchDismissIconAriaLabel: "Close search",
            overflowMenuTriggerText: "More",
            overflowMenuTitleText: "All",
            overflowMenuBackIconAriaLabel: "Back",
            overflowMenuDismissIconAriaLabel: "Close menu"
          }}
        />
      )}
      <AppLayout
        headerSelector="#header"
        ref={appLayout}
        contentType="table"
        navigationOpen={navigationOpen}
        onNavigationChange={handleNavigationChange}
        navigation={
          <SideNavigation 
            items={ITEMS} 
            header={["AWS Voice Assistant"]} 
            activeHref={activeNavHref} 
            onFollow={handleNavItemClick} 
          />
        }
        navigationWidth={200}
        content={
          currentPage === "voice-chat" ? <VoiceAgent /> : <div />
        }
      />
    </div>
  );
}

export default App;
