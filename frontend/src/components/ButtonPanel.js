import React from "react";

const ButtonPanel = ({ nodeData, handleUserSelection }) => {
  const nextOptions = nodeData?.nextOptions || [];

  return (
    <div className="button-panel">
      {nextOptions.map((option, index) => (
        <button key={index} onClick={() => handleUserSelection(option.next, option.text, option.action)}>
          {option.text}
        </button>
      ))}
    </div>
  );
};

export default ButtonPanel;
