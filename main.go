package main

import (
  "os"
  "fmt"

  tea "github.com/charmbracelet/bubbletea"
)

func main() {
  p := tea.NewProgram(New())
  if err := p.Start(); err != nil {
    fmt.Printf("%v", err)
    os.Exit(1)
  }
}
