package main

import (
  "log"
  "google.golang.org/api/gmail/v1"
)

type userConfig struct {
  Gmail string `json:"gmail"`
  Limit int `json:"limit"`
}

type messageTLDR struct {
  from string
  subject string
}

func getFilteredMessages(
  srv *gmail.Service, user string, filter string,
) *gmail.ListMessagesResponse {
  r, err := srv.Users.Messages.List(user).Q(filter).Do()
  if err != nil { log.Fatalf("Unable to retrieve messages: %v", err) }
  return r
}

func getMessageDetails(srv *gmail.Service, user string, messageId string) messageTLDR {
  msg, err := srv.Users.Messages.Get(user, messageId).Format("full").Do()
  if err != nil { log.Println("error when getting mail content: ", err) }
  var tldr messageTLDR = messageTLDR{}
  for _, head := range msg.Payload.Headers {
    if head.Name == "From" {tldr.from = head.Value }
    if head.Name == "Subject" { tldr.subject = head.Value }
  }
  return tldr
}


