import React from 'react'
import styled, { css } from 'styled-components'

export const Button = styled.button`
  display: inline-block;
  padding: 4px 10px;
  margin-bottom: 0;
  font-size: 14px;
  font-weight: normal;
  line-height: 1.42857143;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  -ms-touch-action: manipulation;
  touch-action: manipulation;
  cursor: pointer;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  background-image: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  
  color: #333; 
  background-color: #fff;
  
  :disabled {
    opacity: 0.4;
  }
  
  :hover {
    box-shadow: 0 0 2px gray;
  }
  
  ${props =>
    props.primary &&
    css`
      color: #fff;
      background: #0275d8;
      border-color: #0275d8;
    `}
  
  ${props =>
    props.success &&
    css`
      color: #fff;
      background: #5cb85c;
      border-color: #5cb85c;
    `}
  
  ${props =>
    props.info &&
    css`
      color: #fff;
      background: #5bc0de;
      border-color: #5bc0de;
    `}
  
  ${props =>
    props.warning &&
    css`
      color: #fff;
      background: #f0ad4e;
      border-color: #f0ad4e;
    `}
  
   ${props =>
     props.danger &&
     css`
       color: #fff;
       background: #d9534f;
       border-color: #d9534f;
     `}
`

export default Button